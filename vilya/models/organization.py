# -*- coding: utf-8 -*-

from __future__ import absolute_import
from datetime import datetime
from vilya.libs.store import OrzField, store, IntegrityError, OrzBase


class Organization(OrzBase):
    __orz_table__ = "organizations"
    name = OrzField(as_key=OrzField.KeyType.DESC)
    description = OrzField()
    owner_id = OrzField(as_key=OrzField.KeyType.DESC)
    creator_id = OrzField(as_key=OrzField.KeyType.DESC)
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
        p = None
        try:
            p = cls.create(**kw)
        except IntegrityError:
            store.rollback()
        return p
