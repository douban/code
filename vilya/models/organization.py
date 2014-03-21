# -*- coding: utf-8 -*-

from __future__ import absolute_import
from vilya.models import ModelField, BaseModel


class Organization(BaseModel):
    __table__ = "organizations"
    user_id = ModelField(as_key=ModelField.KeyType.ONLY_INDEX)
    owner_id = ModelField(as_key=ModelField.KeyType.DESC)
    creator_id = ModelField(as_key=ModelField.KeyType.DESC)
    created_at = ModelField(auto_now_create=True)
    updated_at = ModelField(auto_now=True)

    @property
    def user(self):
        from vilya.models.user import User
        user = User.get(self.user_id)
        return user

    @property
    def name(self):
        return self.user.name

    @property
    def description(self):
        return self.user.description

    @property
    def email(self):
        return self.user.email
