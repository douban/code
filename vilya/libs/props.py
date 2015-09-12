# coding: utf-8

"""
提供props常见操作支持，需要对应的类支持get_uuid, 目前是IData
"""

from json import dumps as encode, loads as decode
from .store import bdb


class PropsMixin(object):

    @property
    def _props_name(self):
        '''
        为了保证能够与corelib.mixin.wrapper能和谐的工作
        需要不同的class有不同的__props以免冲突
        '''
        return '__%s/props_cached' % self.get_uuid()

    @property
    def _props_db_key(self):
        return '%s/props' % self.get_uuid()

    def _get_props(self):
        props = bdb.get(self._props_db_key) or ''
        props = props and decode(props) or {}
        return props

    def _set_props(self, props):
        bdb.set(self._props_db_key, encode(props))

    def _destory_props(self):
        bdb.delete(self._props_db_key)

    get_props = _get_props
    set_props = _set_props

    props = property(_get_props, _set_props)

    def set_props_item(self, key, value):
        props = self.props
        props[key] = value
        self.props = props

    def delete_props_item(self, key):
        props = self.props
        props.pop(key, None)
        self.props = props

    def get_props_item(self, key, default=None):
        return self.props.get(key, default)

    def incr_props_item(self, key):
        n = self.get_props_item(key, 0)
        n += 1
        self.set_props_item(key, n)
        return n

    def decr_props_item(self, key, min=0):
        n = self.get_props_item(key, 0)
        n -= 1
        n = n > 0 and n or 0
        self.set_props_item(key, n > min and n or min)
        return n

    def update_props(self, data):
        props = self.props
        props.update(data)
        self.props = props


class PropsItem(object):
    def __init__(self, name, default=None, output_filter=None):
        self.name = name
        self.default = default
        self.output_filter = output_filter

    def __get__(self, obj, objtype):
        r = obj.get_props_item(self.name, None)
        if r is None:
            return self.default
        elif self.output_filter:
            return self.output_filter(r)
        else:
            return r

    def __set__(self, obj, value):
        obj.set_props_item(self.name, value)

    def __delete__(self, obj):
        obj.delete_props_item(self.name)
