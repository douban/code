# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import shutil
import logging
import re
from datetime import datetime

from vilya.config import DOMAIN, DEVELOP_MODE
from vilya.libs import gyt
from vilya.libs.permdir import get_repo_root
from vilya.libs.text import format_md_or_rst
from vilya.libs.store import store, mc, cache, ONE_DAY, IntegrityError
from vilya.libs.props import PropsMixin
from vilya.libs.validators import check_project_name
from vilya.libs.signals import (
    repo_create_signal, repo_watch_signal, repo_fork_signal)
from vilya.models.hook import CodeDoubanHook
from vilya.models.git import GitRepo
from vilya.models.ngit.repo import ProjectRepo
from vilya.models.user import User
from vilya.models.inbox import Inbox
from vilya.models.consts import (
    PROJECT_BC_KEY, MIRROR_HTTP_PROXY, NOTIFY_ON, PERM_PUSH, PERM_ADMIN)
from vilya.models.project_conf import make_project_conf
from vilya.models.utils import linear_normalized
from vilya.models.project_issue import ProjectIssue
from vilya.models.tag import TagMixin, TAG_TYPE_PROJECT_ISSUE
from vilya.models.release import get_unreleased_commit_num
from vilya.models.lru_counter import (
    ProjectOwnLRUCounter, ProjectWatchLRUCounter)
from vilya.models.milestone import Milestone
from vilya.models.utils.switch import WhiteListSwitch
from ellen.utils import JagareError
from vilya.models.nproject import ProjectWatcher

MCKEY_PROJECT = 'code:project:%s:v2'
MCKEY_PROJECT_ID_BY_NAME = 'code:project_id:name:%s'
MCKEY_PROJECT_IDS_BY_OWNER_SORTBY_SUMUP = 'code:project_ids:sumup:%s'

PROPS_LANGUAGE_KEY = 'language'
PROPS_LANGUAGES_KEY = 'languages'


class CodeDoubanProject(PropsMixin, TagMixin):

    def __init__(self, id, name, owner_id, summary, time, product,
                 git_path, trac_conf, fork_from=None, origin_project_id=None,
                 intern_banned=None, can_push=None, mirror_url=None,
                 mirror_proxy=None):

        self.id = id
        self.name = name
        self.owner_id = owner_id
        self.summary = summary
        self.time = time
        self.product = product
        self.git_path = git_path
        self.trac_conf = trac_conf
        self.fork_from = fork_from
        self.can_push = can_push
        self.origin_project_id = origin_project_id or self.id
        self._conf = None
        self.intern_banned = intern_banned
        self.index_name = name.replace('/', '_')
        self.mirror_url = mirror_url
        self.mirror_proxy = mirror_proxy
        self._repo = None

    def __repr__(self):
        return '<CodeDoubanProject %s>' % self.name

    def __eq__(self, other):
        return isinstance(other, CodeDoubanProject) and self.id == other.id

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.id)

    def __str__(self):
        return self.name

    @property
    def dashboard_enabled(self):
        dashboard_enabled_switch = WhiteListSwitch(
            'DASHBOARD_ENABLED_PROJECTS')
        enabled_projects = dashboard_enabled_switch.get()
        return self.name in enabled_projects

    @property
    def deploy_link_enabled(self):
        deploy_link_enabled_switch = WhiteListSwitch(
            'DEPLOY_LINK_ENABLED_PROJECTS')
        enabled_projects = deploy_link_enabled_switch.get()
        return self.name in enabled_projects

    @property
    def url(self):
        return '/%s/' % self.name

    @property
    def repo_url(self):
        return "%s/%s" % (DOMAIN, self.name)

    @property
    def full_url(self):
        hostname = re.sub(r'http[s]?://', '', DOMAIN)
        return '%s/%s' % (hostname, self.name)

    @property
    def repository(self):
        return '%s/%s.git' % (DOMAIN, self.name)

    @property
    def ssh_repository(self):
        return 'git@code.dapps.douban.com:%s.git' % self.name

    @property
    def short_summary(self):
        length = len(self.summary)
        return self.summary if length <= 20 else self.summary + "..."

    @property
    def description(self):
        return self.summary

    def as_dict(self):
        return self.get_info(without_commits=True)

    def get_info(self, without_commits=False):
        #authors = self.git.get_gitstats_data().authors
        info = {
            'url': self.repo_url,
            'name': self.name,
            'description': self.summary,
            'product': self.product,
            'watched_count': self.get_watched_count(self.id),
            'committers_count': len(self.committers),
            'forked_count': self.get_forked_count(self.id),
            'open_issues_count': self.n_open_issues,
            'open_tickets_count': self.n_open_tickets,
            'owner': {
                'name': self.owner_name,
                'avatar': User(self.owner_id).avatar_url,
            },
        }
        forked_from = self.get_forked_from()
        if forked_from:
            info.update({"forked_from": forked_from.get_info(without_commits)})
        if not without_commits:
            commit = self.repo.get_commit('HEAD')
            if commit:
                info['last_commit'] = commit.as_dict()
        return info

    def is_admin(self, username):
        return self.has_push_perm(username)

    @property
    def hooks(self):
        rs = store.execute(
            'select hook_id, url, project_id from codedouban_hooks '
            'where project_id=%s', self.id)
        hooks = [CodeDoubanHook(hook_id, url, project_id)
                 for hook_id, url, project_id in rs]
        return hooks

    @property
    def owner_name(self):
        return self.owner_id

    @classmethod
    @cache(MCKEY_PROJECT % '{id}')
    def get(cls, id):
        rs = store.execute(
            "select project_id, project_name, owner_id, summary, "
            "time, product, git_path, trac_conf, fork_from, "
            "origin_project, intern_banned, can_push from codedouban_projects "
            "where project_id = %s", id)
        return rs and cls(*rs[0]) or None

    @classmethod
    @cache(MCKEY_PROJECT_ID_BY_NAME % '{name}')
    def get_id_by_name(cls, name):
        rs = store.execute("select project_id from codedouban_projects "
                           "where project_name = _latin1%s", name)
        return rs[0][0] if rs else None

    @classmethod
    def get_by_name(cls, name):
        id = cls.get_id_by_name(name)
        if not id:
            return None
        return cls.get(id)

    @classmethod
    def gets_by_owner_id(cls, owner_id):
        rs = store.execute("select project_id"
                           " from codedouban_projects"
                           " where owner_id = %s", owner_id)
        ids = [r for r, in rs]
        return [cls.get(id) for id in ids]

    @staticmethod
    def count_by_owner_id(owner_id):
        owner_id = owner_id.strip()
        if not owner_id:
            return 0
        rs = store.execute("select count(1) from codedouban_projects "
                           "where owner_id = %s",
                           owner_id)
        if rs and rs[0]:
            return rs[0][0]
        else:
            return 0

    @classmethod
    def search_by_name(cls, name, limit=None):
        if check_project_name(name.strip()):
            return []
        rs = store.execute("select project_id from codedouban_projects "
                           "where lower(project_name) like %s",
                           "%%%s%%" % name.lower())
        project_ids = [pid for pid, in rs]
        return [cls.get(project_id) for project_id in project_ids][:limit]

    @classmethod
    def search_for_owners(cls, name, limit=None):
        rs = store.execute(
            "select distinct(owner_id) from codedouban_projects "
            "where owner_id like %s", '%' + name + '%')
        return rs and [owner for owner, in rs][:limit]

    @classmethod
    def gets(cls, ids):
        projs = (cls.get(id) for id in ids)
        return [p for p in projs if p]

    @classmethod
    def get_ids(cls, owner=None, created=None):
        if owner and created:
            rs = store.execute(
                "select project_id from codedouban_projects "
                "where owner_id=%s and time>=%s", (owner, created))
        elif owner:
            rs = store.execute(
                "select project_id from codedouban_projects "
                "where owner_id=%s", owner)
        elif created:
            rs = store.execute(
                "select project_id from codedouban_projects "
                "where time>=%s", created)
        else:
            rs = store.execute("select project_id from codedouban_projects")
        return [pid for pid, in rs]

    PROJECTS_SORT_BYS = ['lru', 'sumup']

    @classmethod
    def get_projects(cls, owner=None, sortby=None):
        if sortby and sortby not in CodeDoubanProject.PROJECTS_SORT_BYS:
            return []

        if sortby == 'lru':
            ids = cls.get_ids(owner=owner)
            ProjectOwnLRUCounter(owner, ids).sort()
        elif sortby == 'sumup':
            ids = cls.get_project_ids_sortby_sumup(owner)
        else:
            ids = cls.get_ids(owner=owner)
        results = cls.gets(ids)
        return results

    @classmethod
    @cache(MCKEY_PROJECT_IDS_BY_OWNER_SORTBY_SUMUP % '{owner}', expire=ONE_DAY)
    def get_project_ids_sortby_sumup(cls, owner=None):
        projects = cls.gets(cls.get_ids(owner=owner))

        FORKED_WEIGHT = 2
        UPDATED_WEIGHT = 2
        ORIGIN_WEIGHT = 4

        forked_keys = linear_normalized(
            [CodeDoubanProject.get_forked_count(repo.id)
             for repo in projects])
        updated_keys = linear_normalized([_.repo.get_last_update_timestamp()
                                          for _ in projects])
        origin_keys = [0.9 if _.id == _.origin_project_id else 0.1
                       for _ in projects]

        sort_keys = {}
        for i, repo in enumerate(projects):
            sort_keys[repo.id] = (forked_keys[i] * FORKED_WEIGHT +
                                  updated_keys[i] * UPDATED_WEIGHT +
                                  origin_keys[i] * ORIGIN_WEIGHT) / \
                (FORKED_WEIGHT + UPDATED_WEIGHT + ORIGIN_WEIGHT)
        projects.sort(key=lambda repo: sort_keys[repo.id], reverse=True)
        return [repo.id for repo in projects]

    @classmethod
    def _flush_project_ids_by_owner(cls, owner=None):
        mc.delete(MCKEY_PROJECT_IDS_BY_OWNER_SORTBY_SUMUP % owner)

    @classmethod
    def add_watch(cls, proj_id, user_id):
        try:
            ProjectWatcher.create(project_id=proj_id,
                                  user_id=user_id)
        except IntegrityError:
            return None
        repo_watch_signal.send(
            cls.get(proj_id), project_id=proj_id, author=user_id)

    @classmethod
    def get_watched_count(cls, proj_id):
        return ProjectWatcher.count(project_id=proj_id)

    @classmethod
    def del_watch(cls, proj_id, user_id):
        w = ProjectWatcher.get(user_id=user_id, project_id=proj_id)
        if w:
            w.delete()

    @classmethod
    def has_watched(cls, proj_id, user):
        w = ProjectWatcher.get(user_id=user.name, project_id=proj_id)
        return True if w else False

    @classmethod
    def get_watched_projects_by_user(cls, user, sortby=None):
        rs = ProjectWatcher.gets(user_id=user)
        ids = [r.project_id for r in rs]
        results = cls.gets(ids)
        if sortby:
            results.sort(key=lambda proj:
                         proj.repo.get_last_update_timestamp(), reverse=True)
        return results

    @classmethod
    def get_watched_others_ids_by_user(cls, user):
        # FIXME: "in"
        rs = store.execute('select project_id from codedouban_watches '
                           'where user_id=%s and project_id not in '
                           '(select project_id from codedouban_projects '
                           'where owner_id=%s)', (user, user))
        ids = [proj_id for proj_id, in rs]
        return ids

    @classmethod
    def get_watched_others_projects_by_user(cls, user, sortby=None):
        ids = cls.get_watched_others_ids_by_user(user)

        if sortby == 'lru':
            ProjectWatchLRUCounter(user, ids).sort()

        results = cls.gets(ids)
        return results

    def get_watch_users(self):
        return [User(user_id)
                for user_id in CodeDoubanProject.get_watch_user_ids(self.id)]

    def get_watch_users_by_channel(self, channel='notify'):
        if channel == "notify":
            return self.get_watch_users()
        elif channel == "email":
            return filter(lambda u: u.settings.watching_email == NOTIFY_ON,
                          self.get_watch_users())
        elif channel == "irc":
            return filter(lambda u: u.settings.watching_irc == NOTIFY_ON,
                          self.get_watch_users())

    @classmethod
    def get_watch_user_ids(cls, project_id):
        rs = ProjectWatcher.gets(project_id=project_id)
        return [r.user_id for r in rs]

    @classmethod
    def add_committer(cls, proj_id, user_id):
        try:
            store.execute("insert into codedouban_committers "
                          "(project_id, user_id) values (%s, %s)",
                          (proj_id, user_id))
        except IntegrityError:
            return None
        store.commit()

    @classmethod
    def del_committer(cls, proj_id, user_id):
        store.execute("delete from codedouban_committers "
                      "where user_id=%s and project_id=%s", (user_id, proj_id))
        store.commit()

    @classmethod
    def get_committers_by_project(cls, proj_id):
        rs = store.execute("select user_id from codedouban_committers "
                           "where project_id=%s", proj_id)
        return [User(user_id) for user_id, in rs]

    def has_push_perm(self, user_id):
        perm = self.get_user_perm(user_id)
        if perm is None:
            perm = self.get_group_perm(user_id)
        if perm and perm >= PERM_PUSH:
            return True
        return False

    def get_user_perm(self, user_id):
        if user_id == self.owner_id:
            return PERM_ADMIN
        committers = self.committers
        if User(user_id) in committers:
            return PERM_PUSH

    def get_group_perm(self, user_id):
        from vilya.models.team_group import ProjectGroup
        pgs = ProjectGroup.gets(project_id=self.id)
        perm = None
        for pg in pgs:
            g = pg.group
            if not g:
                continue
            if g.is_member(user_id):
                perm = perm if perm and perm > g.permission else g.permission
        return perm

    @property
    def committers(self):
        return CodeDoubanProject.get_committers_by_project(self.id)

    def fork(self, fork_name, fork_owner):
        return CodeDoubanProject.add(fork_name, fork_owner, self.summary,
                                     self.product, fork_from=self.id)

    def new_fork(self, owner):
        name = "%s/%s" % (owner, self.realname)
        project = CodeDoubanProject.add(name,
                                        owner,
                                        self.summary,
                                        self.product,
                                        fork_from=self.id)
        if project:
            # FIXME: why do this?
            project.update(self.summary, self.product, project.name,
                           self.intern_banned)
        return project

    @classmethod
    def get_forked_count(cls, proj_id):
        # TODO: update tests!!
        rs = store.execute('select count(1) from codedouban_projects where '
                           'origin_project=%s and project_id!=%s',
                           (proj_id, proj_id))
        orig_fork_count = rs[0][0]

        rs = store.execute('select count(1) from codedouban_projects where '
                           'fork_from=%s and project_id!=%s',
                           (proj_id, proj_id))
        fork_count = rs[0][0]

        return orig_fork_count or fork_count

    def get_forked_users(self):
        rs = store.execute('select owner_id from codedouban_projects '
                           'where fork_from=%s', self.id)
        return [User(user_id) for user_id, in rs]

    def get_forked_project(self, owner_id):
        rs = store.execute('select project_id from codedouban_projects '
                           'where fork_from=%s and owner_id=%s',
                           (self.id, owner_id))
        if rs:
            id = rs[0][0]
            return CodeDoubanProject.get(id)

    def get_forked_projects(self):
        rs = store.execute('select project_id from codedouban_projects '
                           'where fork_from=%s', self.id)
        ids = [str(id) for (id,) in rs]
        return CodeDoubanProject.gets(ids)

    def get_forked_from(self):
        if self.fork_from:
            return CodeDoubanProject.get(self.fork_from)
        return None

    def get_fork_network(self):
        rs = store.execute("select project_id from codedouban_projects "
                           "where origin_project=%s", self.origin_project_id)
        ids = [pid for pid, in rs]
        return CodeDoubanProject.gets(ids)

    def validate(self):
        validators = [check_project_name(self.name, 'Project Name')]
        errors = [error for error in validators if error]
        return errors

    # why by name
    @classmethod
    def update(cls, summary, product, name, intern_banned=None):
        project_id = cls.get_id_by_name(name)
        if not project_id:
            return False
        store.execute(
            "update codedouban_projects set summary=%s, product=%s, "
            "intern_banned=%s where project_name=_latin1%s",
            (summary, product, intern_banned, name))
        store.commit()
        cls.clear_mc(project_id)

    def update_summary(self, summary):
        store.execute("update codedouban_projects "
                      "set summary=%s "
                      "where project_id=%s",
                      (summary, self.id))
        store.commit()
        self.clear_mc(self.id)

    def update_product(self, product):
        store.execute("update codedouban_projects "
                      "set product=%s "
                      "where project_id=%s",
                      (product, self.id))
        store.commit()
        self.clear_mc(self.id)

    def update_intern_banned(self, banned):
        store.execute("update codedouban_projects "
                      "set intern_banned=%s "
                      "where project_id=%s",
                      (banned, self.id))
        store.commit()
        self.clear_mc(self.id)

    def update_can_push(self, can_push):
        push = 1 if can_push else 0
        store.execute("update codedouban_projects "
                      "set can_push=%s "
                      "where project_id=%s",
                      (push, self.id))
        store.commit()
        self.clear_mc(self.id)

    @classmethod
    def add(cls, name, owner_id, summary='', product=None, fork_from=None,
            create_trac=False, intern_banned=None, mirror=None):
        # TODO: add project blacklist
        assert ' ' not in name, "Cannot create a project with spacey name"
        git_path = "%s.git" % name

        try:
            proj_id = store.execute(
                "insert into codedouban_projects "
                "(project_name, owner_id, summary, time, product, "
                "git_path, trac_conf, fork_from, intern_banned) values "
                "(%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (name, owner_id, summary, datetime.now(),
                 product, git_path, name, fork_from, intern_banned))
        except IntegrityError:
            raise
            return None

        if fork_from is not None:
            origins = store.execute("select origin_project from "
                                    "codedouban_projects "
                                    "where project_id=%s", fork_from)
            origin_id, = origins[0]
        else:
            origin_id = proj_id
        store.execute("update codedouban_projects set origin_project=%s "
                      "where project_id=%s", (origin_id, proj_id))
        store.commit()
        cls.clear_mc(proj_id)

        project = cls.get(proj_id)
        # TODO: split create_repo, fork_repo, mirror_repo
        # create git repo
        if fork_from:
            orig_proj = cls.get(fork_from)
            orig_proj.fork_repo(project)
        elif mirror:
            from queues_handler import mirror_projects_add
            mirror_projects_add(mirror, git_path, proj_id)
        else:
            project.create_repo()

        if not mirror:
            project.update_hooks()

        cls._flush_project_ids_by_owner(owner_id)
        if fork_from:
            repo_fork_signal.send(
                project, project_id=proj_id, author=owner_id)
        else:
            repo_create_signal.send(
                project, project_id=proj_id, creator=owner_id)
        return project

    # FIXME: clean property about git
    # all git things
    @property
    def git(self):
        return GitRepo(self.git_real_path, project=self)

    @property
    def repo(self):
        if not self._repo:
            self._repo = ProjectRepo(self)
        return self._repo

    @property
    def default_branch(self):
        return self.repo.default_branch

    @property
    def default_sha(self):
        return self.repo.sha(self.default_branch)

    def update_hooks(self):
        hook_dir = os.path.join(self.repo_path,
                                'hooks')
        link = False if DEVELOP_MODE else True
        gyt.update_hook(hook_dir, link)

    # TODO: remove this
    @classmethod
    def create_git_repo(cls, git_path):
        git_path = os.path.join(get_repo_root(), git_path)
        #check_call(['git', 'init', '--bare', git_path])
        gyt.repo(git_path, init=True)

    # TODO: remove this
    def clone_git(self, to_path):
        git_path = os.path.join(self.repo_root_path, self.git_path)
        to_path = os.path.join(self.repo_root_path, to_path)
        rep = gyt.repo(git_path)
        rep.clone(to_path)

    # TODO: 统一git路径
    @property
    def git_dir(self):
        git_path = os.path.join(self.repo_root_path, self.git_path)
        return git_path

    # TODO: 统一git路径
    # FIXME: remove this, please use project.repo_path
    @property
    def git_real_path(self):
        return os.path.join(self.repo_root_path, '%s.git' % self.name)
    # end git things

    @property
    def conf(self):
        if not self._conf:
            self._conf = make_project_conf(self.name, self.repo)
        return self._conf

    def get_onimaru_url(self, id, project=None):
        if self.conf is None:
            return None
        domain = 'http://onimaru.intra.douban.com'
        if project is None:
            # example:
            # onimaru: /subject/movie
            project = self._conf.get('onimaru', '')
            if not project:
                return None
        project = project.strip()
        if not project.startswith('/'):
            project = '/' + project
        return '{0}{1}/group/{2}/'.format(domain, project, id)

    @property
    def redirect_url(self):
        return "%s/%s/" % (DOMAIN, "hub")

    @property
    def realname(self):
        return self.name.rpartition("/")[-1]

    def put_in_wsgi_environ(self, environ):
        environ['hub.project'] = self

    @classmethod
    def get_from_wsgi_environ(cls, environ):
        return environ.get('hub.project')

    @property
    def owner(self):
        return User(self.owner_id)

    def is_owner(self, user):
        return user and user.name == self.owner.name

    @property
    def forked(self):
        if self.fork_from:
            return CodeDoubanProject.get(self.fork_from)

    def delete(self):
        from vilya.models.nteam import TeamProjectRelationship
        shutil.rmtree(self.git_real_path, ignore_errors=True)
        for hook in self.hooks:
            hook.destroy()
        ProjectWatcher.deletes(project_id=self.id)
        store.execute("delete from codedouban_projects "
                      "where project_id=%s", (self.id,))
        store.commit()
        self.clear_mc(self.id)

        CodeDoubanProject._flush_project_ids_by_owner(self.owner_id)
        rs = TeamProjectRelationship.gets(project_id=self.id)
        for r in rs:
            r.delete()

    def get_actions(self):
        user = PROJECT_BC_KEY % (self.owner_id, self.name)
        return Inbox.get(user=user).get_actions()

    @classmethod
    def exists(cls, name):
        return bool(cls.get_id_by_name(name))

    def transfer_to(self, user):
        sql = ("update codedouban_projects "
               "set owner_id=%s where owner_id=%s and project_id=%s")
        store.execute(sql, (user, self.owner_id, self.id))
        store.commit()
        self.clear_mc(self.id)

    def transfer_to_top(self, user=None):
        new_user = user if user else self.owner_id
        sql = ("update codedouban_projects set project_name=%s, "
               "git_path=%s, trac_conf=%s, owner_id=%s "
               "where owner_id=%s and project_id=%s")
        store.execute(sql, (self.realname, self.realname, self.realname,
                            new_user, self.owner_id, self.id))
        store.commit()
        self.clear_mc(self.id)

    def rename(self, repo_name):
        sql = ("update codedouban_projects set project_name=%s, "
               "git_path=%s where owner_id=%s and project_id=%s")
        if check_project_name(repo_name):
            return False
        if '/' in self.name:
            project_name = "%s/%s" % (self.owner_id, repo_name)
        else:
            project_name = repo_name
        git_path = "%s.git" % project_name
        store.execute(sql, (project_name, git_path, self.owner_id, self.id))
        if self._move(git_path):
            self.git_path = git_path
            self.name = project_name
            store.commit()
        else:
            return False

    def _move(self, git_path):
        base_path = self.repo_root_path
        new_path = os.path.join(base_path, git_path)
        if os.path.exists(git_path):
            return False
        else:
            shutil.move(self.git_dir, new_path)
            return True

    @property
    def n_open_issues(self):
        return ProjectIssue.get_count_by_project_id(self.id, "open")

    @property
    def n_open_tickets(self):
        from vilya.models.ticket import Ticket
        return Ticket.get_count_by_proj(self.id)

    @property
    def n_closed_issues(self):
        return ProjectIssue.get_count_by_project_id(self.id, "closed")

    def get_uuid(self):
        return "/project/%s" % self.id

    @property
    def language(self):
        return self.get_props_item(PROPS_LANGUAGE_KEY, '')

    @language.setter
    def language(self, value):
        self.set_props_item(PROPS_LANGUAGE_KEY, value)

    @property
    def languages(self):
        return self.get_props_item(PROPS_LANGUAGES_KEY, {})

    @languages.setter
    def languages(self, value):
        self.set_props_item(PROPS_LANGUAGES_KEY, value)

    def doc_tabs(self):
        try:
            doc_tabs = []
            if self.conf['docs']:
                sorted_docs = []
                for k, v in self.conf['docs'].items():
                    if not isinstance(v, dict):
                        sorted_docs.append((k, k, k, k))
                    else:
                        sorted_docs.append((v.get('sort', k), k,
                                            v.get('name', k),
                                            v.get('dir', k)))
                sorted_docs.sort()
                sorted_docs = [(_[1], _[2], _[3]) for _ in sorted_docs]
                for doc, name, s_path in sorted_docs:
                    doc_tabs.append((doc, '/docs/%s' % doc, name, s_path))
        except Exception, err:
            logging.warning("Error in config: %r" % err)
            return [('', '', '#ERROR_IN_CONFIG!')]
        return doc_tabs

    @property
    def tag_type(self):
        return TAG_TYPE_PROJECT_ISSUE

    # FIXME: remove this, please use project.mirror
    @property
    def is_mirror_project(self):
        from vilya.models.mirror import CodeDoubanMirror
        return CodeDoubanMirror.get_by_project_id(self.id) is not None

    @property
    def unreleased_commit_num(self):
        return get_unreleased_commit_num(self)

    @property
    def mirror(self):
        from vilya.models.mirror import CodeDoubanMirror
        mirror = CodeDoubanMirror.get_by_project_id(self.id)
        return mirror if mirror else None

    def fetch(self):
        mirror = self.mirror
        env = {}
        if mirror and mirror.with_proxy:
            env['HTTP_PROXY'] = MIRROR_HTTP_PROXY
            env['HTTPS_PROXY'] = MIRROR_HTTP_PROXY
        return self.repo.fetch_(q=True, env=env)

    @property
    def repo_path(self):
        return os.path.join(get_repo_root(), '%s.git' % self.name)

    def fork_repo(self, project):
        self.repo.clone(project.repo_path, bare=True)

    # TODO: use project instead of url
    def mirror_repo(self, url, bare=None, proxy=None):
        env = None
        if proxy:
            env = {
                'HTTP_PROXY': MIRROR_HTTP_PROXY,
                'HTTPS_PROXY': MIRROR_HTTP_PROXY
            }
        ProjectRepo.mirror(url, self.repo_path, env=env)

    def create_repo(self):
        ProjectRepo.init(self.repo_path)

    @property
    def readme(self):
        # TODO: remove tree loop
        ref = self.default_branch
        repo = self.repo
        try:
            tree = repo.get_tree(ref)
        except JagareError as e:
            logging.warning("JagareError: %r" % e)
            return ''
        for item in tree:
            if (item['type'] == 'blob'
                and (item['name'] == 'README'
                     or item['name'].startswith('README.'))):
                readme_content = repo.get_file_by_ref("%s:%s" % (
                    ref, item['path']))
                return format_md_or_rst(item['path'], readme_content)
        return ''

    @property
    def issue_milestones(self):
        rs = Milestone.gets_by_project(self)
        return rs

    @property
    def repo_root_path(self):
        return get_repo_root()

    @property
    def open_parent_pulls(self):
        from vilya.models.ticket import Ticket
        from vilya.models.pull import PullRequest
        pulls = []
        parent = self.get_forked_from()
        if parent:
            pulls = [PullRequest.get_by_proj_and_ticket(parent.id,
                                                        t.ticket_id)
                     for t in Ticket.gets_by_proj(parent.id,
                                                  limit=9999)]
            pulls = [p for p in pulls
                     if p and p.from_proj and p.from_proj.id == self.id]
        return pulls

    @property
    def open_family_pulls(self):
        return self.open_parent_pulls + self.open_pulls

    @property
    def open_network_pulls(self):
        from vilya.models.ticket import Ticket
        from vilya.models.pull import PullRequest
        pulls = []
        projects = self.get_fork_network()
        for project in projects:
            ps = [PullRequest.get_by_proj_and_ticket(project.id,
                                                     t.ticket_id)
                  for t in Ticket.gets_by_proj(project.id,
                                               limit=9999)]
            pulls.extend([p for p in ps
                          if p and p.from_proj and p.from_proj.id == self.id])
        return pulls + self.open_pulls

    @property
    def open_pulls(self):
        from vilya.models.ticket import Ticket
        from vilya.models.pull import PullRequest
        pulls = [PullRequest.get_by_proj_and_ticket(self.id,
                                                    t.ticket_id)
                 for t in Ticket.gets_by_proj(self.id,
                                              limit=9999)]
        return pulls

    def get_pulls_by_commit_shas(self, sha):
        prs = self.open_pulls
        return [pr for pr in prs
                if sha in pr.get_commits_shas()]

    @property
    def groups(self):
        from vilya.models.team_group import ProjectGroup
        rs = ProjectGroup.gets(project_id=self.id)
        return [r.group for r in rs]

    @property
    def remote_name(self):
        remote_name = 'hub/' + self.name
        remote_name = remote_name.replace('~', '_')
        return remote_name

    @classmethod
    def clear_mc(cls, id_):
        project = cls.get(id_)
        if project:
            mc.delete(MCKEY_PROJECT_ID_BY_NAME % project.name)
        mc.delete(MCKEY_PROJECT % id_)

    @classmethod
    def clear_pull(cls, name, pull_id):
        project = cls.get_by_name(name)
        if not project:
            return None
        from vilya.models.pull import PullRequest
        pull = PullRequest.gets_by(to_project=project.id, ticket_id=pull_id,
                                   force_flush=True)
        if pull:
            return True
        return None
