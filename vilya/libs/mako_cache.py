# -*- coding: utf-8 -*-

from vilya.libs.store import mc, ONE_HOUR
from mako.cache import CacheImpl, register_plugin


class McCacheImpl(CacheImpl):
    """基于mc的页面cache实现"""

    def __init__(self, cache):
        self.cache = cache

    def get_or_create(self, key, creation_function, **kw):
        r = mc.get(key)
        if r is None:
            r = creation_function()
            expiretime = kw.get('timeout', ONE_HOUR)
            mc.set(key, r, expiretime)
        return r

    def set(self, key, value, **kw):
        expiretime = kw.get('timeout', ONE_HOUR)
        mc.set(key, value, expiretime)

    def get(self, key, **kw):
        return mc.get(key)

    def invalidate(self, key, **kw):
        mc.delete(key)


register_plugin("mccache", __name__, "McCacheImpl")
