#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from vilya.config import DOMAIN
from datetime import datetime
from dispatches import BaseDispatcher

__all__ = ('dispatch', )


class NotificationDispatcher(BaseDispatcher):
    def __init__(self, data):
        self._uid = self._gen_uid()
        self._data = data

    def _gen_uid(self):
        t = time.time()
        t1 = int(t)
        t2 = int((t-t1)*10E6)
        return "%x%x" % (t1, t2)

    @property
    def uid(self):
        return self._uid

    @property
    def msgs(self):
        return []

    @property
    def hook_url(self):
        return self.domain("/hub/beacon/%s.gif/" % self.uid)

    def now(self):
        return datetime.now()

    def domain(self, url):
        return DOMAIN + url

    def dispatch(self):
        for msg in self.msgs:
            if msg:
                msg.send()

    @staticmethod
    def save_as_attr(func):
        func_name = func.func_name
        if func_name == 'data':
            func_name = '_attr_data'
        else:
            func_name = '_' + func_name

        def _(self):
            if hasattr(self, func_name):
                return getattr(self, func_name)
            else:
                r = func(self)
                setattr(self, func_name, r)
                return r
        return _
