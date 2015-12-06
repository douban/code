# -*- coding: utf-8 -*-

import os
import logging
logging.getLogger().setLevel(logging.DEBUG)
from datetime import datetime

from vilya.libs.props import PropsMixin
from vilya.libs.model import BaseModel, ModelField
from vilya.libs.store import cache, store
from vilya.models.consts import PULL_REF_H, PULL_REF_M
from vilya.models.ticket import Ticket, TicketNode
from vilya.models.ngit.repo import PullRepo, ProjectRepo
from vilya.models.project import CodeDoubanProject
from vilya.config import DOMAIN

# mc keys, ('{self.id}', '{self.from_sha}', '{self.to_sha}')
MC_KEY_PULL_MERGE_BASE = 'PullRequest:%s:%s:%s:merge_base'
MC_KEY_PULL_IS_MERGABLE = 'PullRequest:%s:%s:%s:is_auto_mergable'
MC_KEY_PULL_ID_BY_PID_AND_TID = 'PullRequest:%s:%s:pull_id'
MC_KEY_PULL_COMMITS = 'PullRequest:%s:%s:%s:commits'


class PullMixin(object):

    def __init__(self, from_project_id, from_project_ref,
                 to_project_id, to_project_ref):
        self.from_project = from_project_id
        self.from_branch = from_project_ref
        self.to_project = to_project_id
        self.to_branch = to_project_ref
        self.merged = None
        self.ticket = None
        self.ticket_id = None
        self.mixin = True
        self.init_pull()
        self.sync()

    def init_pull(self):
        if self.merged:
            merged = self.merged.split('..')
            self._from_sha = merged[0]
            self._to_sha = merged[1]
        else:
            self._from_sha = None
            self._to_sha = None

    @property
    def repo(self):
        return PullRepo(self)

    @property
    def family_id(self):
        project = self.to_proj
        if project:
            return project.origin_project_id

    @property
    def from_ref(self):
        return self.from_branch

    @property
    def to_ref(self):
        return self.to_branch

    @property
    def same(self):
        return self.from_proj == self.to_proj

    @property
    def to_proj(self):
        return CodeDoubanProject.get(self.to_project)

    @property
    def from_proj(self):
        return CodeDoubanProject.get(self.from_project)

    @property
    def to_proj_str(self):
        return "%s:%s" % (self.to_proj, self.to_branch)

    @property
    def from_proj_str(self):
        return "%s:%s" % (self.from_proj, self.from_branch)

    @property
    def from_sha(self):
        if self._from_sha is None:
            self._from_sha = self.repo.from_sha
        return self._from_sha

    @property
    def to_sha(self):
        if self._to_sha is None:
            self._to_sha = self.repo.to_sha
        return self._to_sha

    @property
    def from_commit(self):
        return self.from_proj.repo.get_commit(self.from_sha)

    @property
    def to_commit(self):
        return self.to_proj.repo.get_commit(self.to_sha)

    @property
    def to_head_ref(self):
        return PULL_REF_H % self.ticket_id

    @property
    def to_merge_ref(self):
        return PULL_REF_M % self.ticket_id

    @property
    def from_head_ref(self):
        if self.from_project == self.to_project:
            return 'refs/heads/%s' % self.from_branch
        return 'refs/remotes/%s/%s' % (self.from_proj.remote_name,
                                       self.from_branch)

    @property
    def from_merge_ref(self):
        return 'refs/heads/%s' % self.to_branch

    @property
    def to_remote_ref(self):
        return "%s/%s" % (self.to_proj.remote_name,
                          self.to_branch)

    @property
    def from_remote_ref(self):
        return "%s/%s" % (self.from_proj.remote_name,
                          self.from_branch)

    def _get_merge_base(self):
        to_sha = self.to_sha
        from_sha = self.from_sha
        # for: from_sha is None
        if to_sha and from_sha:
            merge_base = self.repo.merge_base(to_sha, from_sha)
        else:
            merge_base = None
        merge_base = merge_base.hex if merge_base else to_sha
        return merge_base

    @property
    def merge_base(self):
        return self._get_merge_base()

    def _get_commits(self):
        commits = self.to_proj.repo.get_commits(self.from_sha, self.to_sha)
        return [c for c in commits if c]

    @property
    def commits(self):
        return self._get_commits()

    @property
    def merged_commits(self):
        if not self.merged:
            return []
        return self.commits

    @property
    def can_pull(self):
        from_commit = self.from_proj.repo.get_commit(self.from_ref)
        to_commit = self.to_proj.repo.get_commit(self.to_ref)
        if from_commit and to_commit:
            return True

    def get_diff(self, ref=None, from_ref=None, paths=None, context_lines=3,
                 ignore_space=False, rename_detection=False, linecomments=[],
                 **kw):
        ref = ref or self.from_sha
        from_ref = from_ref or self.merge_base
        return self.repo.get_diff(ref=ref, from_ref=from_ref,
                                  paths=paths,
                                  context_lines=context_lines,
                                  ignore_space=ignore_space,
                                  rename_detection=rename_detection,
                                  linecomments=linecomments,
                                  **kw)

    def update_ref(self):
        ticket = self.ticket
        if not ticket:
            return
        if ticket.closed:
            return
        project = self.to_proj
        project.repo.update_ref(self.to_head_ref,
                                self.from_head_ref)
        project.repo.update_ref(self.to_merge_ref,
                                self.from_merge_ref)

    def update_remote(self):
        if self.from_project == self.to_project:
            return
        from_proj = self.from_proj
        to_proj = self.to_proj
        remotes = to_proj.repo.remotes
        rs = [r['name'] for r in remotes]
        if from_proj.remote_name not in rs:
            to_proj.repo.add_remote(from_proj.remote_name,
                                    from_proj.repo_path)
        to_proj.repo.fetch(from_proj.remote_name)

    def sync(self):
        if self.merged:
            return
        if not self.from_proj:
            return
        assert self.from_proj.origin_project_id == self.family_id
        self.update_remote()
        self.update_ref()

    # TODO
    def insert(self, ticket_id):
        self.ticket_id = ticket_id
        return Pull2.create(from_project=self.from_proj.id,
                            from_branch=self.from_branch,
                            to_project=self.to_proj.id,
                            to_branch=self.to_branch,
                            ticket_id=ticket_id)

    def is_auto_mergable(self):
        return self.repo.can_merge()

    def is_up_to_date(self):
        if self.merged:
            return True
        try:
            commits = self.commits
            has_commits = True if commits else False
        except:
            has_commits = False
        return not has_commits

    def merge(self, operator, commit_message=''):
        message_header = "Merge pull request #%s from %s:%s" % (
            self.ticket_id, self.from_proj, self.from_ref)
        message_body = commit_message
        commit_sha = self.repo.merge(operator, message_header, message_body)
        return commit_sha

    def pull_clone(self, path):
        ref = self.to_ref
        proj = self.to_proj
        proj.repo.clone(path, bare=False, branch=ref, shared=True)
        repo = ProjectRepo.init(os.path.join(path, '.git'), path, bare=False)
        return repo

    def pull_fetch(self, repo):
        if self.from_project == self.to_project:
            ref = self.pull_fetch_local(repo)
        else:
            ref = self.pull_fetch_remote(repo)
        return ref

    def pull_fetch_remote(self, repo):
        # hotfix:
        from_proj = self.from_proj
        repo.add_remote(from_proj.remote_name,
                        from_proj.repo_path)
        repo.fetch_all()
        return self.from_remote_ref

    def pull_fetch_local(self, repo):
        repo.fetch_all()
        ref = 'origin/%s' % self.from_ref
        return ref

    def pull_merge(self, repo, ref, env, msg, commit_message):
        if not commit_message:
            repo.merge(ref, msg, no_ff=True, _env=env)
        else:
            repo.merge(ref, msg, commit_message, no_ff=True, _env=env)
        repo.push('origin', self.to_ref)


class Pull2(BaseModel, PropsMixin, PullMixin):
    __orz_table__ = "pullreq"
    from_project = ModelField(as_key=ModelField.KeyType.DESC)
    from_branch = ModelField(as_key=ModelField.KeyType.DESC)
    to_project = ModelField(as_key=ModelField.KeyType.DESC)
    to_branch = ModelField(as_key=ModelField.KeyType.DESC)
    merged = ModelField(as_key=ModelField.KeyType.DESC)
    ticket_id = ModelField(as_key=ModelField.KeyType.DESC)

    class OrzMeta:
        id2str = True
        cache_ver = "v1"

    def get_uuid(self):
        return '/pull/%s' % self.id

    def after_create(self):
        self.init_pull()
        self.sync()

    @classmethod
    def get(cls, **kwargs):
        r = super(Pull2, cls).get(**kwargs)
        if r:
            r.init_pull()
            r.sync()
        return r

    @property
    @cache(MC_KEY_PULL_MERGE_BASE % ('{self.id}',
                                     '{self.from_sha}',
                                     '{self.to_sha}'))
    def merge_base(self):
        return self._get_merge_base()

    @property
    @cache(MC_KEY_PULL_COMMITS % ('{self.id}',
                                  '{self.from_sha}',
                                  '{self.to_sha}'))
    def commits(self):
        return self._get_commits()

    @property
    def ticket(self):
        if not self.ticket_id:
            return None
        ticket = Ticket.get_by_projectid_and_ticketnumber(self.to_proj.id,
                                                          self.ticket_id)
        return ticket

    @property
    def full_url(self):
        return "%s/%s/pull/%s/" % (DOMAIN,
                                   self.to_proj.name,
                                   self.ticket_id)

    def get_commits_by_status(self, status):
        if status == 'closed':
            return self.merged_commits
        return self.commits

    def get_commits(self):
        return self.commits

    def get_commits_shas(self):
        return [c.sha for c in self.commits]

    def get_format_patch(self):
        text = self.to_proj.repo.get_patch_file(self.from_sha, self.merge_base)
        return text

    def get_diff_tree(self):
        text = self.to_proj.repo.get_diff_file(self.from_sha, self.merge_base)
        return text

    # TODO: cache
    def get_diff_length(self, ref=None, from_ref=None, paths=None):
        ref = ref or self.from_sha
        from_ref = from_ref or self.merge_base
        return self.repo.get_diff_length(ref=ref, from_ref=from_ref,
                                         paths=paths)

    def get_contexts(self, ref, path, line_start, line_end):
        return self.repo.get_contexts(ref, path, line_start, line_end)

    @classmethod
    def get_by_proj_and_ticket(cls, proj_id, tid):
        return cls.get(to_project=proj_id, ticket_id=tid)

    @classmethod
    def get_by_ticket(cls, ticket):
        proj_id = ticket.project_id
        tid = ticket.ticket_id
        return cls.get(to_project=proj_id, ticket_id=tid)

    @classmethod
    def get_by_from_and_to(cls, from_project, from_branch,
                           to_project, to_branch):
        rs = cls.gets(from_project=from_project,
                      from_branch=from_branch,
                      to_project=to_project,
                      to_branch=to_branch)
        return rs

    @classmethod
    # backward compatibility
    def get_max_ticket_id(cls, proj_id):
        rs = store.execute("select max(ticket_id) "
                           "from pullreq where to_project=%s",
                           (proj_id,))
        r = rs and rs[0]
        if r and r[0]:
            return int(r[0])

    @cache(MC_KEY_PULL_IS_MERGABLE % ('{self.id}',
                                      '{self.from_sha}',
                                      '{self.to_sha}'))
    def is_auto_mergable(self):
        return self.repo.can_merge()

    def can_fastforward(self):
        return self.repo.can_fastforward()

    # TODO: remove this
    def remove_branch_if_temp(self):
        if self.from_ref.startswith('patch_tmp'):
            try:
                self.to_proj.repo.delete_branch(self.from_ref)
            except AssertionError as err:
                logging.debug("Unable to remove_temp_branch(%s): %s" % (
                    self.from_ref, err))

    def is_temp_pull(self):
        if self.from_ref.startswith('patch_tmp'):
            return True

    def _save_merged(self, operator, from_sha, to_sha, merge_commit_sha):
        self.merged = "%s..%s" % (from_sha, to_sha)
        self.save()
        merged_time = datetime.now()
        self.merge_by = operator
        self.merge_time = merged_time.strftime('%Y-%m-%d %H:%M:%S')
        # FIXME: pullreq without ticket_id?
        if self.ticket_id:
            ticket = Ticket.get_by_projectid_and_ticketnumber(
                self.to_proj.id, self.ticket_id)
            if ticket:
                # add commits to ticket
                ticket.add_commits(merge_commit_sha, operator)
                TicketNode.add_merge(ticket.id, operator, merged_time)

    def _get_merge_by(self):
        return self.props.get('merge_by')

    def _set_merge_by(self, merge_by):
        self.set_props_item('merge_by', merge_by)

    merge_by = property(_get_merge_by, _set_merge_by)

    def _get_merge_time(self):
        return self.props.get('merge_time')

    def _set_merge_time(self, merge_time):
        self.set_props_item('merge_time', merge_time)

    def _base_repo_as_dict(self):
        # TODO: wrap to project repo
        d = self._repo_as_dict(self.to_proj)
        commit = self.to_commit
        ts = commit.author_timestamp if commit else 0
        d['repo']['pushed_at'] = datetime.fromtimestamp(
            float(ts)).strftime('%Y-%m-%dT%H:%M:%S')
        d['label'] = "%s:%s" % (self.to_proj.name, self.to_ref)
        d['sha'] = commit.sha if commit else None
        d['ref'] = self.to_ref

        return d

    def _head_repo_as_dict(self):
        d = self._repo_as_dict(self.from_proj)
        if not d['repo']:
            return d

        commit = self.from_commit
        if commit:
            ts = commit.author_timestamp if commit else 0
            d['repo']['pushed_at'] = datetime.fromtimestamp(
                float(ts)).strftime('%Y-%m-%dT%H:%M:%S')
            d['label'] = "%s:%s" % (self.from_proj.name, self.from_ref)
            d['sha'] = commit.sha if commit else None
            d['ref'] = self.from_ref

        return d

    def _repo_as_dict(self, proj):
        if not proj:
            return {'repo': {}}

        d = {}
        d['repo'] = {}
        d['repo']['id'] = proj.id
        d['repo']['name'] = proj.name
        d['repo']['clone_url'] = "%s/%s.git" % (DOMAIN, proj.name)
        d['repo']['html_url'] = "%s/%s" % (DOMAIN, proj.name)

        d['repo']['name'] = proj.name
        d['repo']['summary'] = proj.summary
        d['repo'][
            'fork'] = True if proj.fork_from and proj.fork_from > 0 else False
        d['repo']['created_at'] = proj.time.strftime('%Y-%m-%dT%H:%M:%S')
        d['repo']['author'] = {'login': proj.owner_id}

        return d

    def as_dict(self):
        if not (self.ticket_id and self.to_proj):
            return None

        ticket = Ticket.get_by_projectid_and_ticketnumber(
            self.to_proj.id, self.ticket_id)
        if not ticket:
            return None
        d = {}
        d['url'] = "%s/api/%s/pull/%s" % (
            DOMAIN, self.to_proj.name, self.ticket_id)
        d['html_url'] = "%s/%s/pull/%s/" % (
            DOMAIN, self.to_proj.name, self.ticket_id)
        d['number'] = self.ticket_id  # or ticket_id as name is better?
        d['title'] = ticket.title
        d['description'] = ticket.description
        d['merged'] = self.merged and True or False
        d['created_at'] = ticket.time.strftime('%Y-%m-%dT%H:%M:%S')
        if ticket.closed:
            d['closed_at'] = ticket.closed.strftime('%Y-%m-%dT%H:%M:%S')
            d['state'] = 'closed'
        else:
            d['closed_at'] = None
            d['state'] = 'open'

        if d['merged']:
            # No merged time recored, use closed_at instead
            d['merged_at'] = d['closed_at']
        else:
            d['merged_at'] = None

        d['author'] = {}
        d['author']['login'] = ticket.author
        d['ticket_id'] = self.ticket_id
        d['from_proj'] = self.from_proj and self.from_proj.name or ''
        d['to_proj'] = self.to_proj and self.to_proj.name or ''
        d['to_proj_id'] = self.to_proj and self.to_proj.id or -1
        d['creator'] = ticket.author
        d['base'] = self._base_repo_as_dict()
        d['head'] = self._head_repo_as_dict()
        commits = self.get_commits_by_status(d['state'])
        d['commit_id'] = [c.sha for c in commits]

        return d

    merge_time = property(_get_merge_time, _set_merge_time)

    def get_merged_commit_shas(self):
        commits_shas = []
        for ticket_commits in self.ticket.get_commits():
            commits_shas += [str(c) for c in ticket_commits.commits.split(',')]
        commits_shas = [c for c in commits_shas if c]
        return commits_shas

    def get_merged_commits(self):
        commits = []
        repo = self.to_proj.repo
        commits = filter(None, (repo.get_commit(str(c))
                                for c in self.get_merged_commit_shas()))
        commits = sorted(commits, key=lambda x: x.committer_time, reverse=True)
        if self.merged:
            # exclude last merge commit
            return commits[1:]
        else:
            return commits

    def get_delta_commits(self):
        """
        补充pull request创建之后再提交的commits
        """
        saved = self.get_merged_commit_shas()
        nowcommits = self.get_commits_shas()
        delta_commits = [c for c in nowcommits if c not in saved]
        if delta_commits:
            delta_commits = [self.to_proj.repo.get_commit(str(d))
                             for d in delta_commits]
            delta_commits = filter(None, delta_commits)
            return delta_commits
        return []

    @classmethod
    def open(cls, from_project, from_branch, to_project, to_branch):
        return PullMixin(from_project.id,
                         from_branch,
                         to_project.id,
                         to_branch)
