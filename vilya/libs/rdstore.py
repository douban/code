# coding=utf-8
import redis

from vilya.config import REDIS_HOST, REDIS_PORT, REDIS_DB


def init_store():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)


rdstore = init_store()
rds = rdstore
