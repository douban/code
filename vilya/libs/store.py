# -*- coding: utf-8 -*-

import logging

import libmc
from MySQLdb import connect, IntegrityError  # noqa
from ORZ import setup, OrzField, OrzBase  # noqa
from douban.mc import create_decorators
from douban.sqlstore import store_from_config
from .dbclient import Beansdb
from vilya.config import (
    MEMCACHED_HOSTS, MEMCACHED_CONFIG, MYSQL_STORE, BEANSDBCFG)

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

_clients = {}


def hashdict(d):
    """
    make dictionary becomes a immutable tuple
    """
    if isinstance(d, (tuple, list)):
        return tuple(hashdict(v) for v in d)
    elif isinstance(d, dict):
        return tuple(sorted((k, hashdict(v)) for k, v in d.iteritems()))
    else:
        return d


def Client(servers=None, *args, **kwargs):
    key = hashdict([servers, kwargs])
    mc = _clients.get(key)
    if not mc:
        mc = libmc.Client(servers, *args, **kwargs)
        _clients[key] = mc
    return mc


def get_mc():
    return Client(MEMCACHED_HOSTS, **MEMCACHED_CONFIG)


def get_db():
    return Beansdb(BEANSDBCFG, 16)


def stub_cache(*args, **kws):
    pass

mc = get_mc()
bdb = get_db()

pcache = pcache2 = listcache = cache_in_obj = delete_cache = cache = stub_cache
globals().update(create_decorators(mc))


def mc_gets(mc_key, getter, ids):
    '''helpler for gets function'''
    results = mc.get_multi([mc_key % i for i in ids])
    return [results.get(mc_key % i) or getter(i) for i in ids]


# mysql
def connect_mysql():
    return connect(use_unicode=True, user='root', passwd='', db='valentine')


def make_dict(cursor, row):
    return dict(zip((str(d[0]) for d in cursor.description), row))


def reset_mc(deep=False):
    for mc in _clients.itervalues():
        getattr(mc, 'clear', lambda: True)()
        if deep:
            getattr(mc.mc, 'clear', lambda: True)()


def reset_beansdb():
    for db in _clients.itervalues():
        db.clear_cache()


def clear_beansdb_for_test():
    for db in _clients.itervalues():
        db.clear_cache()
        for s in db.db.servers:
            clear = getattr(s.mc, 'clear', None)
            if clear:
                clear()


def clear_local_cache():
    reset_mc()
    reset_beansdb()


store = store_from_config(MYSQL_STORE, use_cache=False)
setup(store, mc)
