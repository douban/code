# -*- coding: utf-8 -*-

from __future__ import absolute_import
import os
from hashlib import sha1
from datetime import datetime
from vilya.models.session import SessionMixin
from vilya.models import ModelField, BaseModel


class User(BaseModel, SessionMixin):
    __table__ = "users"
    name = ModelField(as_key=ModelField.KeyType.ONLY_INDEX)
    password_digest = ModelField()
    description = ModelField()
    email = ModelField(as_key=ModelField.KeyType.ONLY_INDEX)
    session_id = ModelField()
    session_expired_at = ModelField()
    created_at = ModelField(auto_now_create=True)
    updated_at = ModelField(auto_now=True)

    @classmethod
    def create(cls, **kw):
        kw['password_digest'] = cls.hash_password(kw['password'])
        del kw['password']
        return super(User, cls).create(**kw)

    @property
    def password(self):
        return self.password_digest

    @password.setter
    def _set_password(self, password):
        self.password_digest = self.hash_password(password)

    def validate_password(self, password):
        """Check the password against existing credentials."""
        hashed_pass = sha1()
        hashed_pass.update(password + self.password_digest[:40])
        return self.password_digest[40:] == hashed_pass.hexdigest()

    @classmethod
    def hash_password(cls, password):
        """Hash password on the fly."""

        if isinstance(password, unicode):
            password_8bit = password.encode('UTF-8')
        else:
            password_8bit = password

        salt = sha1()
        salt.update(os.urandom(60))
        hashed = sha1()
        hashed.update(password_8bit + salt.hexdigest())
        password_digest = salt.hexdigest() + hashed.hexdigest()

        if not isinstance(password_digest, unicode):
            password_digest = password_digest.decode('UTF-8')

        return password_digest

    @property
    def projects(self):
        from vilya.models.project import Project
        return Project.gets(owner_id=self.id)

    def to_dict(self):
        return dict(id=self.id,
                    name=self.name)
