# -*- coding: utf-8 -*-
import redis
from vilya.config import REDIS_URI


class Beansdb(object):

    def __init__(self):
        self.redis = redis.from_url(REDIS_URI)

    def get(self, key):
        return self.redis.get(key)

    def set(self, key, value):
        return self.redis.set(key, value)

    def delete(self, key):
        return self.redis.delete(key)
