# -*- coding: utf-8 -*-

from __future__ import absolute_import
import os
import logging
from datetime import datetime
from ellen.utils import JagareError
from vilya.config import DOMAIN
from vilya.libs.permdir import get_repo_root
from vilya.models.git.repo import ProjectRepo
from vilya.models import ModelField, BaseModel
from vilya.config import HOOKS_DIR

KIND_USER = 1
KIND_ORGANIZATION = 2


class Project(BaseModel):
    __table__ = "projects"
    name = ModelField(as_key=ModelField.KeyType.DESC)
    description = ModelField(default='')
    kind = ModelField(as_key=ModelField.KeyType.DESC, default=KIND_USER)
    owner_id = ModelField(as_key=ModelField.KeyType.DESC)
    creator_id = ModelField(as_key=ModelField.KeyType.DESC)
    upstream_id = ModelField(as_key=ModelField.KeyType.DESC)
    family_id = ModelField(as_key=ModelField.KeyType.DESC)
    created_at = ModelField(auto_now_create=True)
    updated_at = ModelField(auto_now=True)

    @BaseModel.transaction
    def fork(self, user_id):
        fork = Project.create(name=self.name,
                              description=self.description,
                              kind=self.kind,
                              owner_id=user_id,
                              creator_id=user_id,
                              upstream_id=self.id,
                              family_id=self.family_id)
        return fork

    @property
    def upstream(self):
        return Project.get(id=self.upstream_id)

    @property
    def forks(self):
        return Project.gets(upstream_id=self.id)

    @property
    def families(self):
        return Project.gets(family_id=self.family_id)

    def to_dict(self):
        return dict(id=self.id,
                    name=self.name,
                    full_name=self.full_name,
                    description=self.description,
                    owner_name=self.owner_name,
                    owner_id=self.owner_id)

    ## git wrap
    @property
    def clone_url(self):
        return "%s%s.git" % (DOMAIN, self.full_name)

    @property
    def full_name(self):
        owner_name = self.owner_name
        if owner_name:
            return '%s/%s' % (owner_name, self.name)
        return "%s" % self.id

    @property
    def repo_path(self):
        return os.path.join(get_repo_root(), '%s.git' % self.id)

    @property
    def owner_name(self):
        from vilya.models.user import User
        from vilya.models.organization import Organization
        if self.kind == KIND_USER:
            user = User.get(id=self.owner_id)
            return user.name
        else:
            org = Organization.get(id=self.owner_id)
            return org.name

    def after_create(self):
        upstream = self.upstream
        if upstream:
            repo = upstream.clone(self.repo_path, bare=True)
        else:
            repo = ProjectRepo.init(self.repo_path)
        repo.update_hooks(HOOKS_DIR)

    @property
    def repo(self):
        if not (hasattr(self, '_repo') and self._repo):
            self._repo = ProjectRepo(self)
        return self._repo
