# -*- coding: utf-8 -*-

from __future__ import absolute_import
import os
import logging
from datetime import datetime
from ellen.utils import JagareError
from vilya.config import DOMAIN
from vilya.libs.permdir import get_repo_root
from vilya.libs.store import OrzField, store, IntegrityError, OrzBase
from vilya.models.git.repo import ProjectRepo

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
        from vilya.models.user import User
        from vilya.models.organization import Organization
        if self.kind == KIND_USER:
            user = User.get_by(id=self.owner_id)
            return user.name
        else:
            org = Organization.get_by(id=self.owner_id)
            return org.name

    # repository

    def init_repo(self):
        from vilya.config import HOOKS_DIR
        repo = ProjectRepo.init(self.repo_path)
        repo.update_hooks(HOOKS_DIR)
        return repo

    def fork_repo(self, project):
        from vilya.config import HOOKS_DIR
        self.repo.clone(project.repo_path, bare=True)
        project.repo.update_hooks(HOOKS_DIR)

    @property
    def repo(self):
        return ProjectRepo(self)

    @property
    def repo_tree(self):
        path = ''
        ref = 'HEAD'
        tree = self.repo.get_tree(ref, path=path)
        return tree

    def get_repo_readme(self, path='/', ref='HEAD'):
        from vilya.libs.text import format_md_or_rst
        repo = self.repo
        try:
            tree = repo.get_tree(ref, path=path)
        except JagareError as e:
            logging.warning("JagareError: %r" % e)
            return ''
        for item in tree:
            if (item['type'] == 'blob'
                and (item['name'] == 'README'
                     or item['name'].startswith('README.'))):
                readme_content = repo.get_file_by_ref("%s:%s" % (ref,
                                                                 item['path']))
                return format_md_or_rst(item['path'], readme_content)
        return ''

    def as_dict(self):
        d = dict(id=self.id,
                 name=self.name,
                 full_name=self.repo_name,
                 description=self.description,
                 owner_name=self.owner_name,
                 owner_id=self.owner_id)
        return d
