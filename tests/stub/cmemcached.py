#!/usr/bin/env python
# -*- coding: utf-8 -*-

from cPickle import dumps, loads

__all__ = ['DIST_MODULA', 'DIST_CONSISTENT', 'DIST_CONSISTENT_KETAMA',
        'Client']

DIST_MODULA = 0
DIST_CONSISTENT = 1
DIST_CONSISTENT_KETAMA = 2

(BEHAVIOR_NO_BLOCK, BEHAVIOR_TCP_NODELAY, BEHAVIOR_HASH, BEHAVIOR_KETAMA,
        BEHAVIOR_SOCKET_SEND_SIZE, BEHAVIOR_SOCKET_RECV_SIZE,
        BEHAVIOR_CACHE_LOOKUPS, BEHAVIOR_SUPPORT_CAS, BEHAVIOR_POLL_TIMEOUT,
        BEHAVIOR_DISTRIBUTION, BEHAVIOR_BUFFER_REQUESTS, BEHAVIOR_USER_DATA,
        BEHAVIOR_SORT_HOSTS, BEHAVIOR_VERIFY_KEY, BEHAVIOR_CONNECT_TIMEOUT,
        BEHAVIOR_RETRY_TIMEOUT, BEHAVIOR_KETAMA_WEIGHTED,
        BEHAVIOR_KETAMA_HASH, BEHAVIOR_BINARY_PROTOCOL, BEHAVIOR_SND_TIMEOUT,
        BEHAVIOR_RCV_TIMEOUT, BEHAVIOR_SERVER_FAILURE_LIMIT) = range(22)


pool = {}

def prepare(val, comp_threshold):
    return dumps(val), 1

def restore(val, flag):
    return loads(val)

def clear():
    for v in pool.values():
        v.clear()

class Client(object):
    def __init__(self, servers=[], dist=DIST_CONSISTENT_KETAMA, debug=0,
            log=None, log_threshold=100000, *a, **kw):
        self.dataset = pool.get(';'.join(servers), {})
        pool[id(self.dataset)] = self.dataset

    def clear(self):
        self.dataset.clear()

    def set(self, key, val, time=0, compress=False):
        _, ver = self.dataset.get(key, (None, 0))
        v = prepare(val, 0)
        self.dataset[key] = (v, ver+1)
        return 1

    def set_multi(self, values, time=0, compress=True):
        for k, v in values.iteritems():
            self.set(k, v, time, compress)
        return 1

    def add(self, key, val, time=0):
        if key not in self.dataset:
            return self.set(key, val, time)
        return 0

    def replace(self, key, val, time=0):
        if key in self.dataset:
            return self.set(key, val, time)
        return 0

    def cas(self, key, val, time=0, cas=0):
        if key in self.dataset:
            _, ver = self.dataset.get(key)
            if ver == cas:
                return self.set(key, val, time)
        return False

    def delete(self, key, time=0):
        if key in self.dataset:
            del self.dataset[key]
        return True

    def delete_multi(self, keys):
        for key in keys:
            self.delete(key)
        return 1

    def get(self, key):
        if key == 'is_stub?':
            return 'yes'
        dummy, ver = self.gets(key)
        if dummy is None:
            return None
        value, flag = dummy
        return restore(value, flag)

    def gets(self, key):
        return self.dataset.get(key, (None, 0))

    def get_multi(self, keys):
        d = {}
        for k in keys:
            v = self.get(k)
            if v is not None:
                d[k] = v
        return d

    def get_list(self, keys):
        return [self.get(key) for key in keys]

    def append(self, key, val, time=0):
        if key in self.dataset:
            self.set(key, str(self.get(key)) + val)
            return 1
        else:
            return 0

    def append_multi(self, keys, val, time=0):
        for k in keys:
            self.append(k, val, time)
        return 1

    def prepend(self, key, val, time=0):
        if key in self.dataset:
            self.set(key, val + str(self.get(key)))
            return 1
        else:
            return 0

    def prepend_multi(self, keys, val, time=0):
        for k in keys:
            self.prepend(k, val, time)
        return 1

    def incr(self, key, val=1):
        if key in self.dataset:
            self.set(key, self.get(key)+val)
            return 0
        else:
            return 16

    def decr(self, key, val=1):
        if key in self.dataset:
            self.set(key, max(self.get(key)-val, 0))
            return 0
        else:
            return 16

    def touch(self, key, exptime):
        return self.delete(key)

    def expire(self, key):
        return self.delete(key)

    def set_behavior(self, flag, behavior):
        pass

    def get_last_error(self):
        return 0
