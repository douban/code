#!/usr/bin/env python
# encoding: utf-8
import os
import glob
import importlib
import logging

from vilya.libs.mq import async


# TODO: dispatcher 的结构需要再调整一次
#       1、现在把notifications分离出来了，事实上这也只是actions这个动作的一部分
#       而notifications里面现在的各种数据format跟逻辑应该塞到 models/actions 里，作为这个action的data
#       2、dispatch操作（send），现在views、models里均会出现不太合理


__all__ = ['dispatch', ]

DISPATCH_MQ_NAME = "dispatches_mq"


def sync_call(module_path, func_names, data):
    logging.info('dispatch functions %s for module %s' %
                 (func_names, module_path))
    module = importlib.import_module(module_path)

    if isinstance(module, type) and issubclass(module, BaseDispatcher):
        dispatcher = module(data)
    else:
        dispatcher = BaseDispatcher(data, module=module)
    dispatcher._call_funcs_sync(func_names)


class BaseDispatcher(object):
    def __init__(self, data, module=None):
        self._data = data
        self._module = module if module else self

    @property
    def exports(self):
        exports = getattr(self._module, '__exports__', None)
        r = exports if exports is not None else dir(self._module)
        return set(r)

    def __enter__(self):
        if self._module is not self:
            _module_enter = getattr(self._module, '__enter__', None)
            if callable(_module_enter):
                self._data = _module_enter(self._data)
        return self

    def __exit__(self, type_, value, traceback):
        if self._module is not self:
            _module_exit = getattr(self._module, '__exit__', None)
            if callable(_module_exit):
                _module_exit(self._data)

    def __call__(self):
        self.dispatch()

    def _call_funcs_sync(self, fnames):
        if not fnames:
            return
        if self._module is self:
            for fn in fnames:
                func = getattr(self._module, fn, None)
                if callable(func):
                    func()
        else:
            for fn in fnames:
                func = getattr(self._module, fn, None)
                if callable(func):
                    func(self._data)

    def _call_funcs_async(self, fnames):
        fnames = list(fnames) if fnames else []
        if not fnames:
            return
        module = getattr(self._module, '__module__', None)
        name = getattr(self._module, '__name__', None)
        if module:
            module_path = '.'.join((module, name))
        else:
            module_path = name
        if module_path:
            async(sync_call)(module_path, fnames, self._data)

    def _call_dispatcher(self, fname):
        if not fname:
            return
        dispatcherClass = getattr(self._module, fname, None)
        if isinstance(dispatcherClass, type) \
                and issubclass(dispatcherClass, BaseDispatcher) \
                and dispatcherClass.__module__ == self._module.__name__:
            dispatcher = dispatcherClass(self._data)
            dispatcher.dispatch()

    def _call_dispatchers(self, dispatchers):
        if not dispatchers:
            return
        for dispatcher in dispatchers:
            self._call_dispatcher(dispatcher)

    def dispatch(self):
        with self as s:
            fnames = self.exports
            self._call_funcs_async(
                [fn for fn in fnames if fn.startswith('async_')])
            self._call_funcs_sync(
                [fn for fn in fnames if fn.startswith('sync_')])
            self._call_dispatchers(
                [fn for fn in fnames if fn.endswith('Dispatcher')])


def get_subpkg():
    dir_ = os.path.dirname(__file__)

    def is_package(d):
        d = os.path.join(dir_, d)
        return os.path.isdir(d) and glob.glob(os.path.join(d, '__init__.py*'))
    subpkgs = filter(is_package, os.listdir(dir_))
    return ['.'.join((__name__, subpkg)) for subpkg in subpkgs]


DISPATCH_BASE_MODULES = get_subpkg()


def dispatch(name, data):
    module = None
    checked_path = []
    for base in DISPATCH_BASE_MODULES:
        path = '.'.join((base, name))
        try:
            module = importlib.import_module(path)
        except ImportError as e:
            checked_path.append(path)
    if module:
        dispatcher = BaseDispatcher(data, module)
        dispatcher.dispatch()
    else:
        return
        raise ImportError(
            'Dispatcher Not Found: checked path %s',
            repr(checked_path))
