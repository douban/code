# -*- coding: utf-8 -*-
from vilya.config import PASSWORD_METHOD
from vilya.models.hashers import check_password, make_password
from vilya.libs.model import BaseModel, ModelField
from vilya.models.consts import (
    USER_ROLE_INTERN, USER_ROLE_STAFF, USER_ROLE_DEFAULT)


class User2(BaseModel):
    __orz_table__ = "users"
    name = ModelField(as_key=ModelField.KeyType.DESC)
    password = ModelField()
    role = ModelField()
    created_at = ModelField(auto_now_create=True)

    class OrzMeta:
        id2str = True

    def __repr__(self):
        return '<u %s, %s>' % (self.id,
                               self.name)

    @property
    def is_intern(self):
        return int(self.role) == USER_ROLE_INTERN

    def validate_password(self, password):
        return check_password(password, self.password)

    @classmethod
    def is_exists(cls, name):
        return cls.get(name=name)

    @classmethod
    def add(cls, name, password):
        encoded_password = make_password(password, hasher=PASSWORD_METHOD)
        return cls.create(name=name, password=encoded_password,
                          role=USER_ROLE_DEFAULT)

    def set_role(self, intern=False):
        self.role = USER_ROLE_INTERN if intern else USER_ROLE_STAFF
        self.save()

    def has_role(self):
        if self.role is not None and \
                int(self.role) != USER_ROLE_DEFAULT:
            return True
