# -*- coding: utf-8 -*-

from __future__ import absolute_import
from code.libs.store import OrzField, store, IntegrityError, OrzBase


class ProjectFork(OrzBase):
    __orz_table__ = "project_forks"
    project_id = OrzField(as_key=OrzField.KeyType.DESC)
    forked_id = OrzField(as_key=OrzField.KeyType.DESC)
    family_id = OrzField(as_key=OrzField.KeyType.DESC)
    creator_id = OrzField(as_key=OrzField.KeyType.DESC)
    created_at = OrzField()

    class OrzMeta:
        id2str = True
