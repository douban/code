# -*- coding: utf-8 -*-
import redis
from vilya.config import REDIS_URI


class Beansdb(object):

    def __init__(self):
        self.redis = redis.from_url(REDIS_URI)

    def get(self, key, default=None):
        data = self.redis.get(key)
        if not data:
            return default
        return data

    def set(self, key, value):
        return self.redis.set(key, value)

    def delete(self, key):
        return self.redis.delete(key)
