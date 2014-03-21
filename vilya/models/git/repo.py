# -*- coding: utf-8 -*-

from __future__ import absolute_import

import os
import time
import gzip
import shutil
import logging
import tempfile
import ConfigParser
from cStringIO import StringIO
from ellen.repo import Jagare
from ellen.utils import JagareError
from vilya.libs.permdir import get_tmpdir
from vilya.models.git.diff import Diff
from vilya.models.git.commit import Commit
from vilya.models.git.blob import Blob
from vilya.models.git.submodule import Submodule
from vilya.models.git.tree import Tree

LATEST_UPDATE_REF_THRESHOLD = 60 * 60 * 24
PULL_REF_H = 'refs/pulls/%s/head'
PULL_REF_M = 'refs/pulls/%s/merge'


class Repo(object):
    provided_features = []

    def __init__(self, path):
        self.type = "repo"
        self.path = path
        self.repo = Jagare(self.path)

    def provide(self, name):
        '''检查是否提供某功能，即是否提供某接口'''
        return name in self.provided_features

    @property
    def is_empty(self):
        return self.repo.empty

    @property
    def default_branch(self):
        branch = None
        head = self.repo.head
        if head:
            branch = head.name.rpartition('/')[-1]
        return branch

    def update_default_branch(self, name):
        branches = self.repo.branches
        if name not in branches:
            return None
        self.repo.update_head(name)

    def update_hooks(self, path):
        self.repo.update_hooks(path)

    def clone(self, path, bare=None, branch=None, mirror=None, env=None):
        self.repo.clone(path,
                        bare=bare, branch=branch,
                        mirror=mirror, env=env)

    def archive(self, name):
        content = self.repo.archive(name)
        outbuffer = StringIO()
        zipfile = gzip.GzipFile(mode='wb', compresslevel=6, fileobj=outbuffer)
        zipfile.writelines(content)
        zipfile.close()
        out = outbuffer.getvalue()
        return out

    def get_submodule(self, ref, path):
        path = path.strip()
        gitmodules = self.repo.show("%s:%s" % (ref, '.gitmodules'))
        if not gitmodules:
            return None
        submodules_lines = gitmodules["data"].split('\n')
        modules_str = '\n'.join([line.strip() for line in submodules_lines])
        config = ConfigParser.RawConfigParser()
        config.readfp(StringIO(modules_str))
        for section in config.sections():
            if config.has_option(section, 'path') \
                    and config.get(section, 'path') == path:
                url = config.get(section, 'url')
                return Submodule(url, path)
        return None

    def get_file(self, ref, path):
        blob = self.repo.show("%s:%s" % (ref, path))
        if not blob:
            return None
        if blob['type'] != 'blob':
            return None
        # TODO: validate blob
        return Blob(self, blob)

    def get_file_by_lines(self, ref, path):
        blob = self.get_file(ref, path)
        # TODO: blob.size < xxx
        if not blob or blob.binary:
            return None
        if not blob.data:
            return []
        src = blob.data
        return src.splitlines()

    def get_file_n_lines(self, ref, path):
        lines = self.get_file_by_lines(ref, path)
        if lines:
            return len(lines)
        return 0

    def get_commits(self, *w, **kw):
        commits = self.repo.rev_list(*w, **kw)
        # TODO: validate commits
        return [Commit(self, commit) for commit in commits]

    def get_raw_diff(self, ref, from_ref=None, **kw):
        ''' get Jagare formated diff dict '''
        return self.repo.diff(ref, from_ref=from_ref, **kw)

    def get_diff(self, ref=None, from_ref=None,
                 linecomments=[], raw_diff=None, **kw):
        ''' get ngit wrapped diff object '''
        _raw_diff = None
        if raw_diff:
            _raw_diff = raw_diff
        elif ref:
            _raw_diff = self.get_raw_diff(ref, from_ref=from_ref, **kw)
        if _raw_diff:
            return Diff(self, _raw_diff, linecomments)
        else:
            return None

    def get_diff_length(self, ref, from_ref=None, **kw):
        _raw_diff = self.get_raw_diff(ref, from_ref=from_ref, **kw)
        return len(_raw_diff['patches']) if _raw_diff else 0

    def get_last_commit(self, ref, path=None):
        if not path:
            return self.get_commit(ref)
        commit = self.repo.rev_list(ref, path=path, max_count=1)
        if not commit:
            return None
        commit = commit[0]
        commit = Commit(self, commit)
        return commit

    def get_commit(self, ref):
        sha = self.repo.resolve_commit(ref)
        if not sha:
            return None
        commit = self.repo.show(sha)
        if not commit:
            return None
        # TODO: validate commit
        return Commit(self, commit)

    def delete_branch(self, name):
        self.repo.delete_branch(name)

    def get_path_by_ref(self, ref):
        ''' get blob or tree '''
        path = self.repo.show(ref)
        if not path:
            return None
        if path['type'] == 'tree':
            path = Tree(self, path['entries'])
        elif path['type'] == 'blob':
            path = Blob(self, path)
        else:
            path = None
        return path

    def get_path(self, ref, path):
        _item = self.repo.show("%s:%s" % (ref, path))
        if not _item:
            return None
        if _item['type'] == 'tree':
            item = Tree(self, _item['entries'])
        elif _item['type'] == 'blob':
            item = Blob(self, _item)
        else:
            item = None
        return item


class ProjectRepo(Repo):
    provided_features = ['project', 'fulltext', 'moreline',
                         'side_by_side', 'patch_actions']

    def __init__(self, project, pull=None):
        self.type = "project"
        self.pull = pull
        self.project = project
        self.project_name = project.name
        self.name = project.name
        self.path = project.repo_path
        self.repo = Jagare(self.path)

    # TODO: url
    @property
    def api_url(self):
        return ''

    @property
    def context_url(self):
        return 'moreline'

    @property
    def fulltext_url(self):
        return 'fulltext'

    @property
    def branches(self):
        return self.repo.branches

    @property
    def tags(self):
        return self.repo.tags

    def get_tree(self, ref, path=None, recursive=False):
        tree = self.repo.ls_tree(ref, path=path, recursive=recursive)
        if not tree:
            return None
        return Tree(self, tree)

    def get_file_by_ref(self, ref):
        blob = self.repo.show(ref)
        if not blob:
            return None
        return blob['data']

    def get_contexts(self, ref, path, line_start, line_end):
        def fix_line_index(index, max_i, min_i=0):
            i = index - 1
            i = max(i, min_i)
            i = min(i, max_i)
            return i
        lines = self.get_file_by_lines(ref, path)
        if not lines:
            return None
        n = len(lines)
        start = fix_line_index(line_start, n)
        end = fix_line_index(line_end, n)
        return lines[start:end]

    def blame_file(self, *w, **kw):
        blame = self.repo.blame(*w, **kw)
        return blame

    def get_renamed_files(self, ref, path=None):
        return self.repo.detect_renamed(ref)

    def commit_file(self, *w, **kw):
        return self.repo.commit_file(*w, **kw)

    def get_temp_branch(self):
        commit = self.get_commit('HEAD')
        return 'patch_tmp' + time.strftime('%Y%m%d%H%M%S-') + commit.sha[10]

    def get_patch_file(self, ref, from_ref=None):
        return self.repo.format_patch(ref, from_ref)

    def get_diff_file(self, ref, from_ref=None):
        _raw_diff = self.get_raw_diff(ref, from_ref)
        if not _raw_diff:
            return ''
        return _raw_diff['diff'].patch

    def get_last_update_timestamp(self):
        commit = self.get_last_commit('HEAD')
        if not commit:
            return 0
        return int(commit.author_timestamp)

    @classmethod
    def init(cls, path, work_path=None, bare=True):
        return Jagare.init(path, work_path=work_path, bare=bare)

    @classmethod
    def mirror(cls, url, path, env=None):
        Jagare.mirror(url, path, env=env)

    def add_remote(self, name, url):
        return self.repo.add_remote(name, url)

    def add_remote_hub(self, name, url):
        self.add_remote('hub/%s' % name, url)

    def update_ref(self, ref, value):
        return self.repo.update_ref(ref, value)

    def sha(self, rev='HEAD'):
        return self.repo.sha(rev)

    def merge_base(self, to_sha, from_sha):
        return self.repo.merge_base(to_sha, from_sha)

    @property
    def remotes(self):
        return self.repo.remotes()

    def fetch_all(self):
        self.repo.fetch_all()

    def fetch(self, name):
        self.repo.fetch(name)

    def archive(self):
        super(ProjectRepo, self).archive(self.project.name)

    def get_latest_update_branches(self):
        refs = self.repo.listall_references()
        refs = filter(lambda r: r.startswith('refs/heads'), refs)
        current_time = time.time()
        latest_branches = []
        for ref in refs:
            commit = self.repo.lookup_reference(ref).get_object()
            commit_time = commit.commit_time
            delta = current_time - commit_time
            if delta < LATEST_UPDATE_REF_THRESHOLD:
                latest_branches.append((commit_time, ref.split('/')[-1]))
        return sorted(latest_branches, key=lambda r: r[0], reverse=True)

    def get_all_src_objects(self):
        refs = self.repo.listall_references()
        refs = filter(lambda r: r.startswith('refs/heads'), refs)
        commits_dict = {}
        for ref in refs:
            commits = self.repo.rev_list(ref)
            commits = {c['sha']: c for c in commits}
            commits_dict.update(commits)
        commits = sorted(commits_dict.values(),
                         key=lambda x: x['time'],
                         reverse=True)

        pruned_set = set()
        objects_dict = {}
        treenode_list = [(commit['sha'],
                          commit['tree'],
                          '') for commit in commits]
        while treenode_list:
            commit_id, tree_id, path = treenode_list.pop()
            if tree_id in pruned_set:
                continue
            pruned_set.add(tree_id)
            objects = self.repo.ls_tree(tree_id, size=True)
            for obj in objects:
                obj_id = obj['id']
                obj_path = '%s/%s' % (path, obj['name'])
                if obj['type'] == 'tree':
                    treenode_list.append((commit_id, obj_id, obj_path))
                elif obj['type'] == 'blob':
                    if obj_id not in objects_dict:
                        commit = commits_dict[commit_id]
                        committer = commit['committer']['name']
                        objects_dict[obj_id] = dict(path=obj_path[1:],
                                                    commit=commit_id,
                                                    size=obj['size'],
                                                    commit_time=commit['time'],
                                                    committer=committer)
        return objects_dict

    def get_readme(self, path='/', ref='HEAD'):
        from vilya.libs.text import format_md_or_rst
        try:
            tree = self.get_tree(ref, path=path)
        except JagareError as e:
            logging.warning("JagareError: %r" % e)
            return ''
        for item in tree:
            if (item['type'] == 'blob'
                and (item['name'] == 'README'
                     or item['name'].startswith('README.'))):
                readme_content = self.get_file_by_ref("%s:%s" % (ref,
                                                                 item['path']))
                return format_md_or_rst(item['path'], readme_content)
        return ''


class GistRepo(Repo):
    provided_features = []

    # TODO: move to utils
    PREFIX = 'gistfile'

    def __init__(self, gist):
        self.type = "gist"
        self.gist = gist
        self.name = gist.name
        self.path = gist.repo_path
        self.repo = Jagare(gist.repo_path)

    @classmethod
    def init(cls, gist):
        Jagare.init(gist.repo_path, bare=True)

    def clone(self, gist):
        super(GistRepo, self).clone(gist.repo_path, bare=True)

    def get_files(self):
        files = []
        if self.empty:
            return files
        tree = self.repo.ls_tree('HEAD')
        for f in tree:
            files.append([f['sha'], f['name']])
        return files

    # TODO: move to utils
    def check_filename(self, fn):
        for c in (' ', '<', '>', '|', ';', ':', '&', '`', "'"):
            fn = fn.replace(c, '\%s' % c)
        fn = fn.replace('/', '')
        return fn

    def commit_all_files(self, names, contents, oids, author):
        data = []
        for i, (name, content, oid) in enumerate(zip(names, contents, oids),
                                                 start=1):
            if not name and not content:
                continue
            if not name:
                name = self.PREFIX + str(i)
            name = self.check_filename(name)
            data.append([name, content, 'insert'])
        files = self.get_files()
        for sha, name in files:
            if name in names:
                continue
            data.append([name, '', 'remove'])
        self.repo.commit_file(branch='master',
                              parent='master',
                              author_name=author.name,
                              author_email=author.email,
                              message=' ',
                              reflog=' ',
                              data=data)

    def is_commit(self, ref):
        commit = self.repo.show(ref)
        if commit:
            return True


class PullRepo(ProjectRepo):
    provided_features = ProjectRepo.provided_features + ['show_inline_toggle']

    def __init__(self, pull):
        super(PullRepo, self).__init__(pull.upstream_project, pull)
        self.type = "pull"
        self.origin_repo = None
        try:
            self.origin_repo = ProjectRepo(pull.origin_project, pull) \
                if pull.origin_project else None
        except JagareError:
            self.origin_repo = None
        self._temp_dir = None

    # TODO: 统一 url
    @property
    def api_url(self):
        project_name = self.project.name
        pull_id = self.pull.pull_id
        # FIXME: pull/new，没有ticket
        if not pull_id:
            return ''
        url = "/api/%s/pull/%s/" % (project_name, pull_id)
        return url

    @property
    def context_url(self):
        project_name = self.project.name
        pull_id = self.pull.pull_id
        # FIXME: pull/new，没有ticket
        if not pull_id:
            return ''
        url = "/api/%s/pull/%s/moreline" % (project_name, pull_id)
        return url

    @property
    def fulltext_url(self):
        project_name = self.project.name
        pull_id = self.pull.pull_id
        # FIXME: pull/new，没有ticket
        if not pull_id:
            return ''
        url = "/api/%s/pull/%s/fulltext" % (project_name, pull_id)
        return url

    @property
    def temp_dir(self):
        if self._temp_dir:
            return self._temp_dir

        # TODO: move to Jagare
        pulltmp = os.path.join(get_tmpdir(), "pulltmp")
        if not os.path.exists(pulltmp):
            os.makedirs(pulltmp)
        worktree = tempfile.mkdtemp(dir=pulltmp)
        self._temp_dir = worktree
        return worktree

    def init(self):
        path = os.path.join(self.temp_dir, '.git')
        work_path = self.temp_dir
        return Jagare.init(path, work_path=work_path, bare=False)

    @property
    def origin_sha(self):
        sha = None
        try:
            sha = self.sha(self.upstream_head_ref)
        except:
            pass
        try:
            if not sha and self.origin_repo:
                sha = self.origin_repo.sha(self.pull.origin_project_ref)
        except:
            pass
        return sha

    @property
    def upstream_sha(self):
        sha = None
        try:
            sha = self.sha(self.pull.upstream_merge_ref)
        except:
            pass
        try:
            if not sha:
                sha = self.sha(self.pull.upstream_project_ref)
        except:
            pass
        return sha

    def merge(self, merger, message_header, message_body):
        env = make_git_env(merger)

        worktree = self.temp_dir
        merge_commit_sha = None
        try:
            if self.pull.is_up_to_date:
                return ''

            from_sha = self.origin_sha
            to_sha = self.upstream_sha
            repo = self.pull.pull_clone(worktree)
            ref = self.pull.pull_fetch(repo)
            repo.merge(ref, message_header, message_body, no_ff=True, _env=env)
            repo.push('origin', self.pull.upstream_project_ref)
            merge_commit_sha = self.sha(self.pull.upstream_project_ref)
            self.pull._save_merged(merger.name, from_sha, to_sha)
        finally:
            shutil.rmtree(worktree)
        return merge_commit_sha

    @property
    def can_merge(self):
        worktree = self.temp_dir
        try:
            user = self.pull.upstream_project.owner
            env = make_git_env(user)
            repo = self.pull.pull_clone(worktree)
            ref = self.pull.pull_fetch(repo)
            result = repo.merge(ref, msg='automerge', _raise=False, _env=env)
            errcode = result['returncode']
        finally:
            shutil.rmtree(worktree)
        return errcode == 0

    @property
    def is_fastforward(self):
        if not self.get_commits(self.upsteam_sha, self.origin_sha):
            return True


def make_git_env(user=None, is_anonymous=False):
    env = {}
    if is_anonymous:
        env['GIT_AUTHOR_NAME'] = 'anonymous'
        env['GIT_AUTHOR_EMAIL'] = 'anonymous@douban.com'
        env['GIT_COMMITTER_NAME'] = 'anonymous'
        env['GIT_COMMITTER_EMAIL'] = 'anonymous@douban.com'
    else:
        env['GIT_AUTHOR_NAME'] = user.name
        env['GIT_AUTHOR_EMAIL'] = user.email
        env['GIT_COMMITTER_NAME'] = user.name
        env['GIT_COMMITTER_EMAIL'] = user.email
    return env
