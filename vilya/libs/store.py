# -*- coding: utf-8 -*-

import logging
from MySQLdb import IntegrityError, connect
from ORZ import OrzField, OrzBase, setup
from douban.mc import mc_from_config, create_decorators
from douban.sqlstore import store_from_config
from vilya.config import MEMCACHED, MYSQL_STORE

logging.getLogger().setLevel(logging.DEBUG)

# mc
ONE_MINUTE = 60
HALF_HOUR = 1800
ONE_HOUR = 3600
HALF_DAY = ONE_HOUR * 12
ONE_DAY = ONE_HOUR * 24
ONE_WEEK = ONE_DAY * 7
ONE_MONTH = ONE_DAY * 30
ONE_YEAR = ONE_DAY * 365


def get_mc():
    return mc_from_config(MEMCACHED, use_cache=False)


def stub_cache(*args, **kws):
    pass

mc = get_mc()
pcache = pcache2 = listcache = cache_in_obj = delete_cache = cache = stub_cache
globals().update(create_decorators(mc))


def mc_gets(mc_key, getter, ids):
    '''helpler for gets function'''
    results = mc.get_multi([mc_key % i for i in ids])
    return [results.get(mc_key % i) or getter(i) for i in ids]


# mysql
def connect_mysql():
    return connect(use_unicode=True)


def make_dict(cursor, row):
    return dict(zip((str(d[0]) for d in cursor.description), row))

store = store_from_config(MYSQL_STORE, use_cache=False)
setup(store, mc)
