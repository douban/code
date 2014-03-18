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
from vilya.models.fork_relationship import ForkRelationship
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
    created_at = ModelField(auto_now_create=True)
    updated_at = ModelField(auto_now=True)

    @BaseModel.transaction
    def fork(self, user_id):
        fork = Project.create(name=self.name,
                description=self.description,
                kind=self.kind,
                owner_id=user_id,
                creator_id=user_id)
        fork_relation = ForkRelationship.create(project_id=fork_project.id,
                forked_id=self.id,
                family_id=self.fork.family_id if self.fork else self.id)
        self.repo.clone(fork.repo_path, bare=True)
        project.repo.update_hooks(HOOKS_DIR)
        return fork

    @property
    def upstream(self):
        rs = ForkRelationship.gets(project_id=self.id)
        return rs[0] if rs else None

    @property
    def forks(self):
        rs = ForkRelationship.gets(forked_id=self.id)
        return [Project.get_by(p.project_id) for p in rs]

    @property
    def families(self):
        id = self.family_id or self.id
        families = ForkRelationship.gets(family_id=id)
        if families:
            return [Project.get(id=family.project_id) for family in families]
        else:
            return []



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
        repo = ProjectRepo.init(self.repo_path)
        repo.update_hooks(HOOKS_DIR)

    @property
    def repo(self):
        if not (hasattr(self, '_repo') and self._repo):
            self._repo = ProjectRepo(self)
        return self._repo

    def to_dict(self):
        return dict(
                id=self.id,
                name=self.name,
                full_name=self.full_name,
                description=self.description,
                owner_name=self.owner_name,
                owner_id=self.owner_id,
                )

