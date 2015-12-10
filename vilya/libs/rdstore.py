# coding=utf-8
import redis

from vilya.config import REDIS_URI


def init_store():
    return redis.from_url(REDIS_URI)


rdstore = init_store()
rds = rdstore
