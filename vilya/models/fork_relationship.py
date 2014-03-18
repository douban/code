# -*- coding: utf-8 -*-

from vilya.models import ModelField, BaseModel


class ForkRelationship(BaseModel):
    __table__ = "fork_relationships"
    project_id = ModelField(as_key=ModelField.KeyType.DESC)
    upstream_id = ModelField(as_key=ModelField.KeyType.DESC)
    family_id = ModelField(as_key=ModelField.KeyType.DESC)
    creator_id = ModelField(as_key=ModelField.KeyType.DESC)
    created_at = ModelField(auto_now_create=True)
