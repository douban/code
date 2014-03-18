# -*- coding: utf-8 -*-

from __future__ import absolute_import
from datetime import datetime
from vilya.models import ModelField, BaseModel


class Organization(BaseModel):
    __table__ = "organizations"
    name = ModelField(as_key=ModelField.KeyType.DESC)
    description = ModelField()
    owner_id = ModelField(as_key=ModelField.KeyType.DESC)
    creator_id = ModelField(as_key=ModelField.KeyType.DESC)
    created_at = ModelField(auto_now_create=True)
    updated_at = ModelField(auto_now=True)
