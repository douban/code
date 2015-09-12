# -*- coding: utf-8 -*-

from __future__ import absolute_import
from binascii import hexlify, Error
from base64 import decodestring

from paramiko import RSAKey, DSSKey, SSHException

from vilya.libs.store import store


# RFC: http://tools.ietf.org/html/rfc4716
class SSHKey(object):

    def __init__(self, id, user_id, key, fingerprint, title):
        self.id = id
        self.user_id = user_id
        self.key = key
        self.fingerprint = fingerprint
        self.title = title

    @property
    def finger(self):
        return self.fingerprint

    @classmethod
    def add(cls, user_id, key):
        fingerprint = generate_fingerprint(key)
        title = generate_title(key)
        id = store.execute(
            'insert into ssh_keys (user_id, `key`, fingerprint, title) '
            'values (%s, %s, %s, %s)',
            (user_id, key, fingerprint, title))
        store.commit()
        return cls(id, user_id, key, fingerprint, title)

    @classmethod
    def validate(cls, user_id, key):
        _key_type, _key, _title = split_ssh_key(key)
        if _key_type not in ('ssh-rsa', 'ssh-dss'):
            return None
        fingerprint = generate_fingerprint(key)
        if not fingerprint:
            return None
        return True

    @classmethod
    def is_duplicated(cls, user_id, key):
        fingerprint = generate_fingerprint(key)
        # FIXME: duplicated fingerprint with user_id
        #        or global fingerprint duplicated?
        rs = store.execute('select id from ssh_keys '
                           'where fingerprint=%s', (fingerprint,))
        if rs and rs[0]:
            return True

    @classmethod
    def gets_by_user_id(cls, user_id):
        rs = store.execute('select id, user_id, `key`, fingerprint, title '
                           'from ssh_keys '
                           'where user_id=%s ', (user_id,))
        if rs:
            return [cls(*r) for r in rs]
        return []

    @classmethod
    def get(cls, id):
        rs = store.execute('select id, user_id, `key`, fingerprint, title '
                           'from ssh_keys '
                           'where id=%s', (id,))
        if rs and rs[0]:
            return cls(*rs[0])

    def delete(self):
        n = store.execute('delete from ssh_keys where id=%s', (self.id,))
        if n:
            store.commit()
            return True

    @classmethod
    def check_own_by_user(cls, user_id, ssh_id):
        rs = store.execute('select id, user_id, `key`, fingerprint, title '
                           'from ssh_keys '
                           'where id=%s and user_id=%s ',
                           (ssh_id, user_id))
        if rs and rs[0]:
            return cls(*rs[0])

    @classmethod
    def get_by_fingerprint(cls, fingerprint):
        rs = store.execute('select id, user_id, `key`, fingerprint, title '
                           'from ssh_keys '
                           'where fingerprint=%s ', (fingerprint,))
        r = rs and rs[0]
        if r:
            return cls(*r)


def split_ssh_key(key):
    _type = None
    _key = None
    _name = None
    fields = key.split(' ')
    length = len(fields)
    if length == 2:
        fields = fields[:2]
        _type, _key = fields
        _name = _type + " " + _key[:18]
    elif length >= 3:
        fields = fields[:3]
        _type, _key, _name = fields
    return (_type, _key, _name)


def generate_title(key):
    _type, _key, _name = split_ssh_key(key)
    return _name


def generate_fingerprint(key):
    fingerprint = None
    _type, _key, _name = split_ssh_key(key)
    try:
        if _type == 'ssh-rsa':
            _key = RSAKey(data=decodestring(_key))
        elif _type == 'ssh-dss':
            _key = DSSKey(data=decodestring(_key))
        else:
            return fingerprint
        hash = hexlify(_key.get_fingerprint())
        fingerprint = ":".join([hash[i:2+i] for i in range(0, len(hash), 2)])
    except SSHException as e:
        # Invalid key
        # raise ValueError(str(e))
        return None
    except Error:
        # Incorrect padding
        # report "Invalid key" error to user
        # raise ValueError("Invalid key")
        return None
    return fingerprint
