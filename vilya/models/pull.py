# -*- coding: utf-8 -*-

import os
from vilya.models import ModelField, BaseModel
from vilya.models.git.repo import (PullRepo,
                                   ProjectRepo,
                                   PULL_REF_M,
                                   PULL_REF_H)


class PullMixin(object):

    def __init__(self, origin_project_id, origin_project_ref,
                 upstream_project_id, upstream_project_ref):
        self.origin_project_id = origin_project_id
        self.origin_project_ref = origin_project_ref
        self.upstream_project_id = upstream_project_id
        self.upstream_project_ref = upstream_project_ref
        self.mixin = True

    # git wrap
    @property
    def repo(self):
        if not (hasattr(self, '_repo') and self._repo):
            self._repo = PullRepo(self)
        return self._repo

    @property
    def upstream_head_ref(self):
        return PULL_REF_H % self.card_id

    @property
    def upstream_merge_ref(self):
        return PULL_REF_M % self.card_id

    @property
    def origin_head_ref(self):
        if self.origin_project_id == self.upstream_project_id:
            return 'refs/heads/%s' % self.origin_project_ref
        return 'refs/remotes/%s/%s' % (self.origin_project_id,
                                       self.origin_project_ref)

    @property
    def origin_merge_ref(self):
        return 'refs/heads/%s' % self.upstream_project_ref

    @property
    def upstream_project(self):
        from vilya.models.project import Project
        return Project.get(id=self.upstream_project_id)

    @property
    def origin_project(self):
        from vilya.models.project import Project
        return Project.get(id=self.origin_project_id)

    @property
    def upstream_remote_ref(self):
        return "%s/%s" % (self.upstream_project.remote_name,
                          self.upstream_project_ref)

    @property
    def origin_remote_ref(self):
        return "%s/%s" % (self.origin_project.remote_name,
                          self.origin_project_ref)

    def update_ref(self):
        project = self.upstream_project
        project.repo.update_ref(self.upstream_head_ref,
                                self.origin_head_ref)
        project.repo.update_ref(self.upstream_merge_ref,
                                self.origin_merge_ref)

    def update_remote(self):
        if self.origin_project_id == self.upstream_project_id:
            return

        upstream = self.upstream_project
        origin = self.origin_project
        remotes = upstream.repo.remotes
        rs = [r.name for r in remotes]
        if origin.remote_name not in rs:
            upstream.repo.add_remote(origin.remote_name,
                                     origin.repo_path)
        upstream.repo.fetch(origin.remote_name)

    @property
    def is_fastforward(self):
        return self.repo.is_fastforward

    @property
    def is_up_to_date(self):
        pass

    @property
    def is_validated(self):
        origin_repo = self.origin_project.repo
        upstream_repo = self.upstream_project.repo
        origin_commit = origin_repo.get_commit(self.origin_project_ref)
        upstream_commit = upstream_repo.get_commit(self.upstream_project_ref)
        if upstream_commit and origin_commit:
            return True

    def merge(self):
        pass

    def sync(self):
        self.update_remote()
        self.update_ref()

    # pull internal git action
    def pull_clone(self, path):
        ref = self.upstream_project_ref
        project = self.upstream_project
        project.repo.clone(path, bare=False, branch=ref)
        repo = ProjectRepo.init(os.path.join(path, '.git'), path, bare=False)
        return repo

    def pull_fetch(self, repo):
        if self.origin_project_id == self.upstream_project_id:
            return self.pull_fetch_local(repo)
        return self.pull_fetch_remote(repo)

    def pull_fetch_remote(self, repo):
        origin = self.origin_project
        repo.repo.add_remote(origin.remote_name,
                             origin.repo_path)
        repo.fetch_all()
        return self.origin_remote_ref

    def pull_fetch_local(self, repo):
        # FIXME: origin_project_ref rule
        repo.fetch_all()
        return 'origin/%s' % self.origin_project_ref

    def pull_merge(self, repo, ref, env, msg, commit_message):
        if not commit_message:
            # TODO: put commit_message to kw
            repo.merge(ref, msg, no_ff=True, _env=env)
        else:
            repo.merge(ref, msg, commit_message, no_ff=True, _env=env)
            repo.push('origin', self.to_ref)


class Pull(BaseModel, PullMixin):
    __table__ = "pulls"
    origin_project_id = ModelField(as_key=ModelField.KeyType.DESC)
    origin_project_ref = ModelField(as_key=ModelField.KeyType.DESC)
    upstream_project_id = ModelField(as_key=ModelField.KeyType.DESC)
    upstream_project_ref = ModelField(as_key=ModelField.KeyType.DESC)
    origin_commit_sha = ModelField()
    upstream_commit_sha = ModelField()
    merged_commit_sha = ModelField()
    merged_at = ModelField()
    card_id = ModelField(as_key=ModelField.KeyType.DESC)
    creator_id = ModelField(as_key=ModelField.KeyType.DESC)
    created_at = ModelField(auto_now_create=True)

    def __repr__(self):
        return "<Pull %s>" % self.id

    def after_create(self):
        self.sync()

    def sync(self):
        card = self.card
        if card and not card.closer_id:
            super(Pull, self).sync()

    @property
    def pull_id(self):
        return self.card.number

    @property
    def card(self):
        from vilya.models.card import Card
        return Card.get(id=self.card_id)

    @classmethod
    def open(cls, origin_project_id, origin_project_ref,
             upstream_project_id, upstream_project_ref):
        pull = PullMixin(origin_project_id,
                         origin_project_ref,
                         upstream_project_id,
                         upstream_project_ref)
        return pull
