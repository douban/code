# -*- coding: utf-8 -*-

from __future__ import absolute_import
import os
from hashlib import sha1
from datetime import datetime
from code.libs.store import OrzField, store, IntegrityError, OrzBase


class User(OrzBase):
    __orz_table__ = "users"
    name = OrzField(as_key=OrzField.KeyType.DESC)
    password = OrzField(as_key=OrzField.KeyType.DESC)
    description = OrzField()
    email = OrzField(as_key=OrzField.KeyType.DESC)
    created_at = OrzField(default='null')
    updated_at = OrzField(default='null')

    class OrzMeta:
        id2str = True

    @classmethod
    def get_by_name(cls, name):
        rs = cls.gets_by(name=name)
        return rs[0] if rs else None

    @classmethod
    def add(cls, **kw):
        now = datetime.now()
        kw['created_at'] = now
        kw['updated_at'] = now
        kw['password'] = cls.hash_password(kw['password'])
        u = None
        try:
            u = cls.create(**kw)
        except IntegrityError:
            store.rollback()
        return u

    # password
    @property
    def hashed_password(self):
        return self.password

    @hashed_password.setter
    def _set_password(self, password):
        self.password = self.hash_password(password)

    def validate_password(self, password):
        """Check the password against existing credentials."""
        hashed_pass = sha1()
        hashed_pass.update(password + self.hashed_password[:40])
        return self.hashed_password[40:] == hashed_pass.hexdigest()

    @classmethod
    def hash_password(cls, password):
        """Hash password on the fly."""
        hashed_password = password

        if isinstance(password, unicode):
            password_8bit = password.encode('UTF-8')
        else:
            password_8bit = password

        salt = sha1()
        salt.update(os.urandom(60))
        hash = sha1()
        hash.update(password_8bit + salt.hexdigest())
        hashed_password = salt.hexdigest() + hash.hexdigest()

        if not isinstance(hashed_password, unicode):
            hashed_password = hashed_password.decode('UTF-8')

        return hashed_password

    @property
    def projects(self):
        from code.models.project import Project
        return Project.gets_by(owner_id=self.id)
