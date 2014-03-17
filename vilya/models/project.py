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

    def add_fork(self, user_id):
        from vilya.models.project_fork import ProjectFork
        fork_project = None
        try:
            fork_project = Project.create(name=self.name,
                                          description=self.description,
                                          kind=self.kind,
                                          owner_id=user_id,
                                          creator_id=user_id)
            fork = ProjectFork.create(project_id=fork_project.id,
                                      forked_id=self.id,
                                      family_id=self.fork.family_id if self.fork else self.id)
        except IntegrityError:
            store.rollback()
        else:
            self.fork_repo(fork_project)
        return fork_project

    @property
    def fork(self):
        from vilya.models.project_fork import ProjectFork
        rs = ProjectFork.gets_by(project_id=self.id)
        return rs[0] if rs else None

    @property
    def fork_projects(self):
        from vilya.models.project_fork import ProjectFork
        rs = ProjectFork.gets_by(forked_id=self.id)
        return [Project.get_by(p.project_id) for p in rs]

    @property
    def family_projects(self):
        from vilya.models.project_fork import ProjectFork
        family_id = self.fork.family_id if self.fork else self.id
        rs = ProjectFork.gets_by(family_id=family_id)
        return [Project.get_by(p.project_id) for p in rs]

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
        from vilya.config import HOOKS_DIR
        repo = ProjectRepo.init(self.repo_path)
        repo.update_hooks(HOOKS_DIR)

    def fork_repo(self, project):
        from vilya.config import HOOKS_DIR
        self.repo.clone(project.repo_path, bare=True)
        project.repo.update_hooks(HOOKS_DIR)

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

