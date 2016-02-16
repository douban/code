# -*- coding: utf-8 -*-

import os
import shutil
from datetime import datetime

from vilya.libs.signals import (
    gist_created_signal, gist_forked_signal, gist_updated_signal)
from vilya.libs.store import store
from vilya.libs import gyt
from vilya.libs.permdir import get_repo_root
from vilya.models.git import GitRepo
from vilya.models.ngit.repo import GistRepo
from vilya.models.user import User
from vilya.models.gist_comment import GistComment
from vilya.models.gist_star import GistStar

from vilya.config import DOMAIN

PAGE_LIMIT = 10
DATETIME_FORMAT = '%Y-%m-%dT%H:%M:%SZ'
GIST_FILE_RAW = DOMAIN + '/gist/%s/raw/master/%s'

PRIVILEGE_PUBLIC = 1
PRIVILEGE_SECRET = 0

SORTS = ('created', 'updated')
DIRECTIONS = ('desc', 'asc')

GIST_NAME = 'gist:%s'


def init_gist_folder():
    GISTS_PATH = os.path.join(get_repo_root(), 'gist')
    if not os.path.exists(GISTS_PATH):
        os.makedirs(GISTS_PATH)

init_gist_folder()


class Gist(object):

    ANONYMOUS = 'anonymous'

    def __init__(self, id, name, description, owner_id, is_public,
                 fork_from, created_at, updated_at):
        self.id = id
        self.name = name.decode('utf-8') or GIST_NAME % id
        self.description = description.decode('utf-8')
        self.owner_id = owner_id
        self.is_public = is_public
        self.fork_from = fork_from
        self.created_at = created_at
        self.updated_at = updated_at

    def __repr__(self):
        return '<Gist name:%s, owner:%s>' % (self.name, self.owner_id)

    def __eq__(self, target):
        return self.id == target.id

    @property
    def repo_root_path(self):
        return get_repo_root()

    def as_dict(self):
        data = {
            'type': 'gist',
            'url': self.url,
            'description': self.description,
            'author': self.owner.name,
        }
        data['time'] = self.created_at.strftime('%Y-%m-%dT%H:%M:%S')
        if self.updated_at:
            data['time'] = self.updated_at.strftime('%Y-%m-%dT%H:%M:%S')
        content = []
        data['content'] = {}
        for path in self.files:
            path = path.encode('utf8')
            blob = self.repo.get_file(path, 'HEAD')
            src = blob if blob else ''
            content.append(path)
            content.append(src)
        data['content'] = '\n'.join(content)
        return data

    @property
    def full_name(self):
        return '%s/%s' % (self.owner_id, self.name)

    # TODO: remove this, please use gist.repo_path
    @property
    def git_real_path(self):
        return os.path.join(self.repo_root_path, 'gist/%s.git' % self.id)

    # TODO: remove this, please use gist.repo
    @property
    def git(self):
        try:
            repo = GitRepo(self.git_real_path)
        except gyt.GytRepoNotInited:
            repo = None
        return repo

    @property
    def git_path(self):
        return 'gist/%s.git' % self.id

    @property
    def git_url(self):
        # TODO(xutao) user namespace
        return '%s/%s' % (DOMAIN, self.git_path)

    @property
    def url(self):
        return '%s/gist/%s/%s' % (DOMAIN, self.owner_id, self.id)

    @property
    def relative_url(self):
        return '/gist/%s/%s' % (self.owner_id, self.id)

    @property
    def download_url(self):
        return self.url + '/download'

    @property
    def embed_url(self):
        return self.url + '.js'

    @property
    def n_star(self):
        rs = store.execute(
            "select count(1) from gist_stars where gist_id=%s", (self.id,))
        return rs[0][0]

    @property
    def stars(self):
        rs = store.execute(
            "select user_id from gist_stars where gist_id=%s", (self.id,))
        return [User(user_id) for user_id, in rs]

    def star(self, user_id):
        if not GistStar.get_by_gist_and_user(self.id, user_id):
            GistStar.add(self.id, user_id)
        return True

    def unstar(self, user_id):
        gs = GistStar.get_by_gist_and_user(self.id, user_id)
        if gs:
            gs.delete()
        return True

    @property
    def n_fork(self):
        rs = store.execute(
            "select count(1) from gists where fork_from=%s", (self.id,))
        return rs[0][0]

    @property
    def forks(self):
        rs = store.execute(
            "select id, name, description, owner_id, is_public, fork_from, "
            "created_at, updated_at from gists where fork_from=%s", (self.id,))
        return [Gist(*r) for r in rs]

    @property
    def n_revision(self):
        if self.repo:
            return len(self.repo.get_commits('HEAD'))
        return 0

    @property
    def n_comments(self):
        rs = store.execute(
            "select count(1) from gist_comments where gist_id=%s", (self.id,))
        return rs[0][0]

    @property
    def n_files(self):
        return len(self.files)

    @property
    def files(self):
        files = []
        for sha, name in self.repo.get_files():
            files.append(name)
        #if not self.repo.empty:
        #    files = [item['path'] for item in self.git._list_tree('HEAD', '')]
        return files

    # TODO: remove this later
    @property
    def list_sha1_with_files(self):
        files = self.repo.get_files()
        return files
        #return self.git.list_sha1_with_files('HEAD')

    @property
    def forked_from(self):
        return Gist.get(self.fork_from)

    def get_revlist_with_renames(self, max_count=3, skip=0, rev='HEAD',
                                 path='', author=None):
        revlist = self.repo.get_commits(rev,
                                        max_count=max_count,
                                        skip=skip,
                                        path=path,
                                        author=author)
        return revlist

    # TODO: remove this, please use gist.fork_repo
    def clone_git(self, to_path):
        git_path = os.path.join(self.repo_root_path, self.git_path)
        to_path = os.path.join(self.repo_root_path, to_path)
        rep = gyt.repo(git_path)
        rep.clone(to_path)

    @property
    def owner(self):
        return User(self.owner_id)

    @property
    def comments(self):
        return GistComment.gets_by_gist_id(self.id)

    @classmethod
    def get(cls, id):
        rs = store.execute(
            "select id, name, description, owner_id, is_public, fork_from, "
            "created_at, updated_at from gists where id=%s", (id,))
        return rs and cls(*rs[0]) or None

    @classmethod
    def gets(cls, ids):
        return [cls.get(id) for id in ids]

    @classmethod
    def add(cls, description, owner_id, is_public, gist_names=[],
            gist_contents=[], fork_from=None):
        now = datetime.now()
        if fork_from:
            name = cls.get(fork_from).name
            id = store.execute(
                "insert into gists "
                "(`name`, `description`, `owner_id`, `created_at`, `fork_from`) "  # noqa
                "values (%s, %s, %s, %s, %s)",
                (name, description, owner_id, now, fork_from))
            store.commit()
            gist = cls.get(id)
            fork_from = cls.get(fork_from)
            fork_from.fork_repo(gist)
            gist_forked_signal.send(gist, gist_id=gist.id)
        else:
            name = cls._get_name(names=gist_names)
            id = store.execute(
                "insert into gists "
                "(`name`, `description`, `owner_id`, `is_public`, `created_at`) "  # noqa
                "values (%s, %s, %s, %s, %s)",
                (name, description, owner_id, is_public, now))
            store.commit()
            gist = cls.get(id)
            gist.create_repo()
            gist._commit_all_files(gist_names, gist_contents, create=True)
            gist_created_signal.send(gist, gist_id=gist.id)
        return gist

    def update(self, description, gist_names=[], gist_contents=[],
               gist_oids=[]):
        name = self._get_name(gist_names)
        store.execute(
            "update gists set name=%s, description=%s, updated_at=%s where id=%s",  # noqa
            (name, description, datetime.now(), self.id))
        store.commit()
        self._commit_all_files(gist_names, gist_contents, gist_oids)
        gist_updated_signal.send(self, gist_id=self.id)

    def _commit_all_files(self, gist_names, gist_contents, gist_oids=[],
                          create=False):
        _gets = lambda x: x if isinstance(x, list) else [x]
        gist_names = _gets(gist_names)
        gist_contents = _gets(gist_contents)
        gist_oids = _gets(gist_oids) or [''] * len(gist_names)

        if create and gist_names and not gist_names[0]:
            gist_names = gist_names * len(gist_contents)
            gist_oids = [''] * len(gist_contents)

        self.repo.commit_all_files(gist_names, gist_contents,
                                   gist_oids, User(self.owner_id))

    @classmethod
    def _get_name(cls, names=[]):
        if not isinstance(names, list):
            names = [names]
        name = names and names[0]
        if name and not name.startswith('gistfile'):
            return name
        return ''

    def fork(self, user_id):
        return Gist.add(
            self.description, user_id, self.is_public, fork_from=self.id)

    @classmethod
    def gets_by_owner(cls, owner_id, is_self=False, start=0, limit=10,
                      sort='created', direction='desc'):
        assert sort in SORTS
        assert direction in DIRECTIONS
        sql = ("select id, name, description, owner_id, is_public, fork_from, "
               "created_at, updated_at from gists where owner_id=%s ")
        if not is_self:
            sql += " and is_public=1 "
        sql += "order by %s %s limit %s, %s" % (
            sort + '_at', direction, start, limit)
        rs = store.execute(sql, owner_id)
        return [cls(*r) for r in rs]

    @classmethod
    def forks_by_user(cls, owner_id, start=0, limit=10, sort='created',
                      direction='desc'):
        assert sort in SORTS
        assert direction in DIRECTIONS
        sortby = "order by %s_at %s " % (sort, direction)
        rs = store.execute(
            "select id, name, description, owner_id, is_public, fork_from, "
            "created_at, updated_at from gists where owner_id=%s and "
            "fork_from!=0 " + sortby + "limit %s, %s",
            (owner_id, start, limit))
        return [cls(*r) for r in rs]

    @classmethod
    def stars_by_user(cls, owner_id, start=0, limit=10, sort=None, direction=None):
        rs = store.execute(
            "select gist_id from gist_stars "
            "where user_id=%s order by id desc limit %s, %s",
            (owner_id, start, limit))
        return filter(None, [cls.get(r) for r, in rs])

    @classmethod
    def publics_by_user(cls, owner_id, start=0, limit=10, sort='created',
                        direction='desc'):
        return cls._privilege_by_user(
            owner_id, start=start, limit=limit, privilege=1,
            sort=sort, direction=direction)

    @classmethod
    def secrets_by_user(cls, owner_id, start=0, limit=10, sort='created',
                        direction='desc'):
        return cls._privilege_by_user(
            owner_id, start=start, limit=limit, privilege=0,
            sort=sort, direction=direction)

    @classmethod
    def _privilege_by_user(cls, owner_id, start=0, limit=10, privilege=1,
                           sort='created', direction='desc'):
        assert sort in SORTS
        assert direction in DIRECTIONS
        sortby = "order by %s_at %s " % (sort, direction)
        rs = store.execute(
            "select id, name, description, owner_id, is_public, fork_from, "
            "created_at, updated_at from gists where owner_id=%s and "
            "is_public=%s " + sortby + "limit %s, %s",
            (owner_id, privilege, start, limit))
        return [cls(*r) for r in rs]

    @classmethod
    def count_user_all(self, owner_id, is_self=False):
        if is_self:
            rs = store.execute(
                "select count(1) from gists where owner_id=%s", (owner_id,))
        else:
            rs = store.execute(
                "select count(1) from gists where owner_id=%s "
                "and is_public=1", (owner_id,))
        return rs[0][0]

    @classmethod
    def count_user_fork(self, owner_id):
        rs = store.execute(
            "select count(1) from gists where owner_id=%s and "
            "fork_from!=0", (owner_id,))
        return rs[0][0]

    @classmethod
    def count_user_star(self, owner_id):
        rs = store.execute(
            "select count(1) from gist_stars where user_id=%s", owner_id)
        return rs[0][0]

    @classmethod
    def count_public_by_user(cls, owner_id):
        return cls._count_privilege_by_user(
            owner_id, privilege=PRIVILEGE_PUBLIC)

    @classmethod
    def count_secret_by_user(cls, owner_id):
        return cls._count_privilege_by_user(
            owner_id, privilege=PRIVILEGE_SECRET)

    @classmethod
    def _count_privilege_by_user(cls, owner_id, privilege=PRIVILEGE_PUBLIC):
        rs = store.execute(
            "select count(1) from gists where owner_id=%s and is_public=%s",
            (owner_id, privilege))
        return rs[0][0]

    def delete(self):
        shutil.rmtree(self.git_real_path, ignore_errors=True)
        store.execute("delete from gists where id=%s", (self.id,))
        store.execute("delete from gist_stars where gist_id=%s", (self.id,))
        store.execute("delete from gist_comments where gist_id=%s", (self.id,))
        store.commit()

    def is_starred(self, user_id):
        rs = store.execute(
            "select id from gist_stars where gist_id=%s and user_id=%s",
            (self.id, user_id))
        return True if rs else False

    @classmethod
    def discover(cls, name, sort='created', direction='desc', start=0,
                 limit=5):
        assert sort in SORTS
        assert direction in DIRECTIONS
        sortby = "order by %s_at %s " % (sort, direction)
        sort = '%s_at' % sort
        reverse = direction == 'desc'
        if name == 'forked':
            rs = store.execute("select distinct(fork_from) from gists "
                               "where fork_from!=0 and is_public=1 " +
                               sortby + "limit %s, %s",
                               (start, limit))
            return [cls.get(r) for r, in rs]
        elif name == 'starred':
            rs = store.execute("select distinct(gist_id) from gist_stars "
                               "order by created_at " +
                               direction + " limit %s, %s",
                               (start, limit))
            gists = filter(None, [cls.get(r) for r, in rs])
            return sorted(gists, key=lambda g: getattr(g, sort),
                          reverse=reverse)
        else:
            rs = store.execute(
                "select id, name, description, owner_id, is_public, "
                "fork_from, created_at, updated_at from gists where "
                "is_public=1 " + sortby + "limit %s, %s",
                (start, limit))
            return [cls(*r) for r in rs]

    @property
    def repo(self):
        return GistRepo(self)

    @property
    def repo_path(self):
        return os.path.join(self.repo_root_path, 'gist/%s.git' % self.id)

    def create_repo(self):
        GistRepo.init(self)

    def fork_repo(self, gist):
        self.repo.clone(gist)

    def get_file(self, path, rev='master'):
        blob = self.repo.get_file(rev, path)
        if not blob:
            # FIXME: value convention
            return False
        return blob.data

    @property
    def updated_time(self):
        commit = self.repo.get_last_commit('HEAD')
        if not commit:
            return 0
        return int(commit.author_timestamp)


def fork_detail(gist):
    return dict(user=user_detail(gist.owner),
                url=gist.url,
                created_at=gist.created_at.strftime(DATETIME_FORMAT))


def user_detail(user):
    return dict(login=user.name, id=user.name, avatar_url=user.avatar_url,
                url=user.url)


def gist_detail(gist, include_forks=False, include_history=False):
    files = {
        f: dict(filename=f, raw_url=GIST_FILE_RAW % (gist.id, f))
        for f in gist.files
    }
    ret = dict(url=gist.url,
               id=gist.id,
               description=gist.description,
               public=bool(gist.is_public),
               user=user_detail(gist.owner),
               files=files,
               comments=gist.n_comments,
               html_url=gist.url,
               git_pull_url=gist.git_url,
               git_push_url=gist.git_url,
               created_at=gist.created_at.strftime(DATETIME_FORMAT))

    if include_forks:
        ret.update(dict(forks=[fork_detail(f) for f in gist.forks]))

    if include_history:
        # TODO
        pass

    return ret
