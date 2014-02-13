# -*- coding: utf-8 -*-

from libs.store import mc


class MLockMeta(type):
    def __getattr__(cls, name):
        return MLock(name)


class MLock(object):
    __metaclass__ = MLockMeta

    def __init__(self, mc_prefix):
        self.mc_prefix = mc_prefix

    def __call__(self, **kw):
        parts = [self.mc_prefix]
        for pair in sorted(kw.items()):
            parts += list(pair)
        mc_key = ':'.join(map(str, parts))
        return MLockContext(mc_key)


class MLockContext(object):
    def __init__(self, mc_key, value=1, expire=30):
        self.mc_key = mc_key
        self.value = value
        self.expire = expire

    def __str__(self):
        return ('<MLockContext(mc_key=%s, value=%s, expire=%s)>'
                % (self.mc_key, self.get_value(), self.expire))

    __repr__ = __str__

    def acquire(self):
        if not mc.add(self.mc_key, self.value, self.expire):
            raise MLockExclusiveError

    def release(self):
        mc.delete(self.mc_key)

    def get_value(self):
        return mc.get(self.mc_key)

    def __enter__(self):
        try:
            self.acquire()
        except MLockExclusiveError as e:
            return e

    def __exit__(self, type_, value, traceback):
        if traceback is None:
            self.release()


class MLockExclusiveError(Exception):
    pass
