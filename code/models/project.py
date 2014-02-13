# -*- coding: utf-8 -*-

from __future__ import absolute_import
import os
from datetime import datetime
from code.config import DOMAIN
from code.libs.permdir import get_repo_root
from code.libs.store import OrzField, store, IntegrityError, OrzBase
from code.models.git.repo import ProjectRepo

KIND_USER = 1
KIND_ORGANIZATION = 2


class Project(OrzBase):
    __orz_table__ = "projects"
    name = OrzField(as_key=OrzField.KeyType.DESC)
    description = OrzField(default='')
    kind = OrzField(as_key=OrzField.KeyType.DESC, default=KIND_USER)
    owner_id = OrzField(as_key=OrzField.KeyType.DESC)
    creator_id = OrzField(as_key=OrzField.KeyType.DESC)
    created_at = OrzField()
    updated_at = OrzField()

    @classmethod
    def get_by_name(cls, name):
        rs = cls.gets_by(name=name)
        return rs[0] if rs else None

    @classmethod
    def get_by_name_and_owner(cls, name, owner_id):
        rs = cls.gets_by(name=name, owner_id=owner_id)
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
        else:
            p.init_repo()
        return p

    ## git wrap
    @property
    def repo_http_url(self):
        # FIXME: use project name
        return "%s%s.git" % (DOMAIN, self.repo_name)

    @property
    def repo_path(self):
        return os.path.join(get_repo_root(),
                            '%s.git' % self.id)

    @property
    def repo_name(self):
        owner_name = self.owner_name
        if owner_name:
            return '%s/%s' % (owner_name, self.name)
        return "%s" % self.id

    @property
    def owner_name(self):
        from code.models.user import User
        from code.models.organization import Organization
        if self.kind == KIND_USER:
            user = User.get_by(id=self.owner_id)
            return user.name
        else:
            org = Organization.get_by(id=self.owner_id)
            return org.name

    # repository

    def init_repo(self):
        from code.config import HOOKS_DIR
        repo = ProjectRepo.init(self.repo_path)
        repo.update_hooks(HOOKS_DIR)
        return repo

    @property
    def repo(self):
        return ProjectRepo(self)

    @property
    def repo_tree(self):
        path = ''
        ref = 'HEAD'
        tree = self.repo.get_tree(ref, path=path)
        return tree

    def as_dict(self):
        d = dict(id=self.id,
                 name=self.name,
                 full_name=self.repo_name,
                 description=self.description,
                 owner_name=self.owner_name,
                 owner_id=self.owner_id)
        return d
