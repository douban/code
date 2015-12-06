# -*- coding: utf-8 -*-
from __future__ import absolute_import

import os
import re
import tempfile
import urllib
import urlparse
import time
import gzip
from datetime import datetime
from cStringIO import StringIO

from pygit2 import GIT_SORT_TIME
from pytz import FixedOffset

from vilya.libs import gyt
from vilya.libs.reltime import compute_relative_time
from vilya.libs.text import email_normalizer
from vilya.libs.text import (
    highlight_code, trunc_utf8, remove_unknown_character)
from vilya.models.user import User, get_author_by_email
from vilya.models.stats import GitDataCollector
from vilya.libs.diff import rehunk
from vilya.models.consts import PATCH_TYPE, MIRROR_HTTP_PROXY
from vilya.models.utils import check_douban_email


_MC_KEY_GYT_CAT = 'gitcat:%s:%s:v02'
_MC_KEY_OBJ_TYPE = 'cat-file-type:%s:%s:v02'
_MC_KEY_BLAME = 'blame'
_MC_KEY_LATEST_COMMIT = 'gitlatestcommit:%s:%s:%s:v03'
_GITSTATS_KEY = 'gitstats:%s:v3'
_GITSTATS_DATA_KEY = 'gitstats_data:%s:%s:v3'
_GITSTATS_YEAR_WEEK_ACT = 'gitstats:year_week_act:%s'
RE_EMAIL = re.compile(r'<(?P<email>.*)>')
RE_HUNK_LIMIT = 500

TEMP_BRANCH_MARKER = 'TEMPORARY_BRANCH'
(REV, NAME, AUTHOR_MAIL, TIME, DISP, SUMM, LINE, SRC) = range(8)


def quote_utf8(s):
    s = s.encode('utf-8')
    return urllib.quote_plus(s)


def unquote_utf8(q):
    s = urllib.unquote_plus(q)
    return s.decode('utf-8')


def _adjust_git_age(age):
    nb, _, rest = age.partition(' ')
    if rest == 'seconds ago' and int(nb) < 10:
        return 'few seconds ago'
    return age


class GitRepo(object):

    def __init__(self, path, work_tree=None, project=None):
        self.path = path
        self.work_tree = work_tree
        self.project = project
        self.project_name = project.name if project else ''
        # TODO check, shouldn't we pass work_tree to gyt repo?
        # be careful it would change a lot of things behind
        # getting not bare repos if inited with work_tree
        self._gyt_repo = gyt.repo(self.path)
        self.pygit2_repo = self._gyt_repo.repo

    def __str__(self):
        if self.project:
            return "<Repo %s>" % self.project.name
        else:
            return "<Repo %s>" % self.path

    def __eq__(self, y):
        return bool(y and isinstance(y, GitRepo) and (
            self.path == y.path and self.project == y.project))

    def call(self, cmd, _raise=True, _raw=False, _env=None):
        return self._gyt_repo.call(cmd, _raise=_raise, _raw=_raw, _env=_env)

    def object_type(self, ref='HEAD', path=None):
        refspec = '%s:%s' % (ref, path) if path is not None else ref

        try:
            sha = self._gyt_repo.sha(ref)
        except Exception, e:
            raise e
        if sha == ref:
            refspec = '%s:%s' % (sha, path) if path is not None else sha
            objt = self._cached_obj_type(refspec)
            return objt
        else:
            return self._gyt_repo.cat(refspec, only_type=True)

    #@cache(_MC_KEY_OBJ_TYPE % ('{self.project_name}', '{refspec}'),
    #       expire=ONE_WEEK)
    def _cached_obj_type(self, refspec):
        return self._gyt_repo.cat(refspec, only_type=True)

    @classmethod
    def clone(cls, repo_url, path):
        gyt.clone(repo_url, path)
        return GitRepo(os.path.join(path, '.git'), work_tree=path)

    def fetch_mirror(self, proxy=None):
        env = {}
        if proxy:
            env['HTTP_PROXY'] = MIRROR_HTTP_PROXY
            env['HTTPS_PROXY'] = MIRROR_HTTP_PROXY
        self._gyt_repo.fetch_mirror(_env=env)

    def cat(self, ref):
        #rs = mc.get(_MC_KEY_GYT_CAT % (self.project_name, ref))
        # if rs:
        #    return rs
        fixed_sha = self._gyt_repo.sha(ref)
        return self._fixed_cat(fixed_sha)

    # @cache(_MC_KEY_GYT_CAT % ('{self.project_name}', '{sha}'),
    #       expire=ONE_WEEK)
    def _fixed_cat(self, sha):
        return self._gyt_repo.cat(sha)

    def latest_commit(self, path, ref='HEAD'):
        fixed_sha = self._gyt_repo.sha(ref)
        return self._latest_commit_fixed(fixed_sha, quote_utf8(path))

    # @cache(_MC_KEY_LATEST_COMMIT % ('{self.project_name}', '{sha}',
    # '{quoted_path}'), expire=ONE_WEEK)
    def _latest_commit_fixed(self, sha, quoted_path):
        path = unquote_utf8(quoted_path)
        commits = self._gyt_repo.rev_list(sha, max_count=1, paths=path)
        if commits and commits[0]:
            return commits[0].hex

    def get_remotes(self):
        return self._gyt_repo.remotes()

    def add_remote(self, name, url):
        name = name.replace('~', '_')
        self._gyt_repo.add_remote(name, url)

    def fetch(self, repo):
        try:
            repo = repo.replace('~', '_')
            remote = [r for r in self.get_remotes() if r.name == repo]
            if len(remote) >= 1:
                remote = remote[0]
                remote.fetch()
        except OSError:
            return

    def get_branches(self):
        '''returns list of (local) branches, with active (= HEAD) one being
        the first item'''
        return gyt.repo(self.path).refs(select='branches', short=True,
                                        current_first=True)

    def get_tags(self):
        return gyt.repo(self.path).refs(select='tags', short=True)

    def get_sha(self, ref, raise_error=False):
        return self._gyt_repo.sha(ref)

    def get_commit(self, sha):
        if self.object_type(sha) != 'commit':
            return None
        c = self.cat(sha)
        parent = c['parent'][-1] if c[
            'parent'] else None  # Weird, why would we want only the last one?
        author_name = c['author']['name']
        author_email = email_normalizer(author_name, c['author']['email'])
        author = User(name=author_name, email=author_email)
        committer_name = c['committer']['name']
        committer_email = email_normalizer(
            committer_name, c['committer']['email'])
        committer = User(name=committer_name, email=committer_email)
        message = (
            c['message'] + '\n\n' + remove_unknown_character(c['body'])).strip()
        author_time = c['author']['date']
        commit_time = c['committer']['date']
        return Commit(
            self.project_name, sha=sha, tree=c['tree'], parent=parent,
            author=author, author_time=author_time, committer=committer,
            commit_time=commit_time, message=message)

    def convert_localtime(self, ts):
        fmt = "%Y-%m-%d %H:%M:%S"
        s = time.strftime(fmt, time.localtime(ts))
        return datetime.strptime(s, fmt)

    def get_3dot_diff(self, sha1, sha2, ignore_space=False, context_lines=3,
                      rename_detection=False):
        """ 对仓库做 git diff sha1...sha2 操作，返回diff对象列表 """
        return self._get_diff(
            sha1, sha2, ignore_space=ignore_space,
            context_lines=context_lines, rename_detection=rename_detection)

    def get_3dot_diff_onefile(self, sha1, sha2, path=None, context_lines=3,
                              paths=None, rename_detection=None):
        assert path or paths
        return self._get_diff(
            sha1, sha2, path, context_lines=context_lines, paths=paths,
            rename_detection=rename_detection)

    def _get_diff(self, sha1, sha2, path=None, ignore_space=False,
                  context_lines=3, rename_detection=False, paths=None):
        diffs = Diffs.from_diffs(
            self._gyt_repo.diff(
                sha1, sha2, path=path, parse_patch=True,
                ignore_space=ignore_space, context_lines=context_lines,
                rename_detection=rename_detection, paths=paths))
        return diffs

    def parse_diff_old_author(self, diff, sha):
        old = []
        byauthor = {}
        bylines = {}
        try:
            blame = self.blame_src(sha, diff.filepath)[1]
        except:
            return {}, {}
        for l in diff.diff_content:
            if l[0] == 'deletion':
                old.append(l[1])
        for o in old:
            try:
                author_email = blame[int(o) - 1][AUTHOR_MAIL]
                if author_email:
                    author = author_email.split('@')[0]
                    byauthor.setdefault(author, []).append(o)
                    bylines[o] = author
            except:
                continue
        return byauthor, bylines

    def get_rev_list(self, sha1, sha2, _raise=True):
        return self._gyt_repo.rev_walk_shas(sha1, sha2)

    def get_range_commits(self, sha1, sha2):
        commits = []
        output = self.get_rev_list(sha1, sha2, _raise=False)
        if output is False:
            return False
        for sha in output:
            commits.append(self.get_commit(sha))
        return commits

    def get_last_update_timestamp(self):
        head_sha = self.get_sha('HEAD')
        if not head_sha:
            return 0
        else:
            return int(self.cat(head_sha)['author']['ts'])

    def get_raw_content(self, fname, ref='HEAD'):
        # This is used with /api/project/raw/app.yaml
        return self.cat('%s:%s' % (ref, fname))

    def get_revisions(self, begin='HEAD~5', end='HEAD'):
        if self.is_empty():
            return []
        res = self.get_rev_list(begin, end, _raise=False)
        revisions = []
        if not res:
            return []
        for commit_sha in res:
            commit = self.cat(commit_sha)
            d = {}
            d['name'] = commit['author']['name']
            d['id'] = commit_sha
            d['date'] = commit['committer']['date'].strftime(
                '%Y-%m-%dT%H:%M:%S') + commit['committer']['tz']
            d['message'] = commit['message']
            if commit['body']:
                # TODO check if really needed
                d['message'] = '\n    '.join(
                    [d['message']] + [''] + remove_unknown_character(
                        commit['body']).splitlines())
            d['email'] = email_normalizer(d['name'], commit['author']['email'])
            # TODO check if merge is really needed
            if len(commit['parent']) > 1:
                d['merge'] = ' '.join(sha[:7] for sha in commit['parent'])
            d['files'] = []
            cmt_obj = self.get_commit(commit_sha)
            if cmt_obj.parent:
                repo = self.pygit2_repo
                cmt = repo.revparse_single(commit_sha)
                parent = cmt.parents[0]
                diffs = parent.tree.diff(cmt.tree)
                for patch in diffs:
                    filepath = patch.new_file_path if patch.status != 'D' \
                        else patch.old_file_path
                    d['files'].append({'type': PATCH_TYPE.get(patch.status),
                                       'filepath': filepath})
            else:
                diffs = self.parse_diff(commit_sha)
                for diff in diffs['difflist']:
                    d['files'].append({
                        'type': diff.type, 'filepath': diff.filepath})
            revisions.append(d)
        return revisions

    def get_src(self, path='', ref='HEAD'):
        obj_type = self.object_type(ref, path)
        if obj_type is False:
            raise IOError("object %s:%s do not exist" % (ref, path))
        if obj_type == 'tree':
            tree = self._list_tree(ref, path)
            tree = sorted(tree, key=lambda x: x['type'], reverse=True)
            return obj_type, tree
        else:
            src = self.cat('%s:%s' % (ref, path))
            return 'blob', src

    def cache_refspec(self, prefix, ref='HEAD', path=''):
        sha = self.get_sha(ref)
        if not sha:
            return
        key = prefix + ':' + sha + ':' + path
        return key

    # @cache(lambda self, ref, path: self.cache_refspec(
    # _MC_KEY_BLAME, ref, path), expire=ONE_WEEK)
    def blame_src(self, ref='HEAD', path=''):
        # Using --porcelain instead of --line-porcelain is more efficient, as
        # commit info (author, time, summary) is displayed only once
        # and it is compatible with git 1.7.5
        res = self._gyt_repo.blame(ref, path)
        res = res.splitlines()
        blame = []
        hl_lines = self._blame_src_highlighted_lines(ref, path)
        rev_data = {}
        new_block = True
        for line in res:
            if new_block:
                sha, old_no, line_no = line.split()[:3]
                if sha not in rev_data:
                    rev_data[sha] = {}
                rev_data[sha]['line_no'] = line_no
                rev_data[sha]['old_no'] = old_no
                new_block = False
            elif line.startswith('author '):
                _, _, author = line.partition(' ')
                rev_data[sha]['author'] = author.strip()
            elif line.startswith('author-time '):
                _, _, time = line.partition(' ')
                time = datetime.fromtimestamp(float(time)).strftime('%Y-%m-%d')
                rev_data[sha]['time'] = time
            elif line.startswith('author-mail '):
                _, _, email = line.partition(' ')
                email = RE_EMAIL.match(email).group('email')
                rev_data[sha]['email'] = email
            elif line.startswith('summary '):
                _, _, summary = line.partition(' ')
                rev_data[sha]['summary'] = summary.strip()
                disp_summary = trunc_utf8(
                    summary.encode('utf-8'), 20).decode('utf-8', 'ignore')
                rev_data[sha]['disp_summary'] = disp_summary
            elif line.startswith('filename'):
                _, _, filename = line.partition(' ')
                rev_data[sha]['filename'] = filename
                filename = trunc_utf8(
                    filename.strip().encode('utf-8'), 30).decode('utf-8', 'ignore')
                rev_data[sha]['disp_name'] = filename
            elif line.startswith('\t'):
                # Try to get an highlighted line of source code
                code_line = hl_lines.get(str(
                    line_no), '').replace('\n', '').decode('utf-8', 'ignore')
                if not code_line:
                    code_line = line[1:]
                blame.append((sha,
                              rev_data[sha]['author'],
                              rev_data[sha]['email'],
                              rev_data[sha]['time'],
                              rev_data[sha]['disp_summary'],
                              rev_data[sha]['summary'],
                              rev_data[sha]['line_no'],
                              rev_data[sha]['old_no'],
                              rev_data[sha]['filename'],
                              rev_data[sha]['disp_name'],
                              code_line,
                              ))
                new_block = True
        return self._blame_src_header(ref), blame

    def blame_one_line(self, ref='HEAD', path='', lineno=1):
        res = self._gyt_repo.blame_line(ref, path, lineno)
        res = res.splitlines()
        sha_line = res[0]
        author_line = res[1]
        time_line = res[3]
        summary_line = res[9]
        sha, _, line_no = sha_line.split()[:3]
        _, _, author = author_line.partition(' ')
        author = author.strip()
        _, _, time = time_line.partition(' ')
        time = datetime.fromtimestamp(float(time)).strftime('%Y-%m-%d')
        _, _, summary = summary_line.partition(' ')
        summary = summary.strip()
        result = {'author': author,
                  'time': time,
                  'sha': sha,
                  'summary': summary
                  }
        return result

    def _blame_src_header(self, ref):
        header_data = self.cat(ref)
        header = {}
        header['message'] = header_data['message']
        header['parents'] = ' '.join(header_data['parent'])
        header['author'] = header_data['author']['name']
        header['email'] = email_normalizer(
            header['author'], header_data['author']['email'])
        header['time'] = compute_relative_time(header_data['author']['ts'])
        return header

    def _blame_src_highlighted_lines(self, ref, path):
        HIGHLIGHT_PATN = re.compile(
            r'<a name="L-(\d+)"></a>(.*?)(?=<a name="L-(?:\d+)">)', re.DOTALL)
        source_code = self.cat('%s:%s' % (ref, path))
        # TODO try to avoid having highlighted content here
        hl_source_code = highlight_code(path, source_code)
        hl_lines = dict(re.findall(HIGHLIGHT_PATN, hl_source_code))
        return hl_lines

    def get_commits(self, path='', ref='HEAD'):
        if self.object_type(ref, path) != 'tree':
            raise IOError('get_commits works on a tree')
        bag = {}
        for item in self._list_tree(ref, path):
            sha = item['id']
            bag[sha] = {
                'id': sha,
                'mode': item['mode'],
                'type': item['type'],
                'name': item['name'],
                'path': item['path'],
            }
            latest_commit_sha = self.latest_commit(item['path'], ref)
            if latest_commit_sha:
                l_com = self.cat(latest_commit_sha)
                user = l_com['author']['email']
                user_t = user.split('@')[0] if '@' in user else user
                bag[sha]['contributor'] = user_t
                if check_douban_email(user):
                    bag[sha]['contributor_url'] = User(user_t).url
                else:
                    bag[sha]['contributor_url'] = False
                bag[sha]['message'] = l_com['message']
                bag[sha]['hash'] = latest_commit_sha
                bag[sha]['age'] = compute_relative_time(l_com['author']['ts'])
            else:
                bag[sha]['contributor'] = ''
                bag[sha]['contributor_url'] = ''
                bag[sha]['message'] = ''
                bag[sha]['hash'] = ''
                bag[sha]['age'] = ''
        return bag

    def get_revlist(self, max_count=20, skip=0, rev='HEAD', path='',
                    author=None, query=None):
        commits = []
        cs = self._gyt_repo.rev_list(rev, max_count=max_count, skip=skip,
                                     paths=path, author=author, query=query)
        for c in cs:
            commit = {}
            commit['parents'] = [p.hex for p in c.parents] if c.parents else ''
            commit['date'] = datetime.fromtimestamp(
                c.committer.time,
                FixedOffset(c.committer.offset))
            commit['age'] = compute_relative_time(c.author.time)
            commit['author'] = c.author.name
            commit['email'] = email_normalizer(c.author.name,
                                               c.author.email)
            message_title = c.message.splitlines()[0] if c.message else ''
            commit['message'] = message_title
            commit['commit'] = c.hex
            commits.append(commit)
        return commits

    def get_gitstats_data(self):
        assert self.project_name
        assert self.project
        repo = self.pygit2_repo
        data = GitDataCollector(self._gyt_repo)
        try:
            # FIXME: GitError: Reference 'refs/heads/master' not found
            head_sha = repo[repo.head.target].hex
            get_author = lambda u: get_author_by_email(
                u.email.encode('utf-8'), u.name.encode('utf-8'))
            authors = {get_author(c.author) for c in repo.walk(
                head_sha, GIT_SORT_TIME)}
            n_author = len(authors)
        except:
            return data
        data.collect(self.path, self.project_name, head_sha, n_author)
        return data

    #@cache(_GITSTATS_YEAR_WEEK_ACT % '{self.project_name}', expire=ONE_WEEK)
    def get_year_week_act_stats(self):
        data = self.get_gitstats_data()
        year_week_act = data.year_week_act
        peak = data.year_week_act_peak
        return peak, year_week_act

    def parse_diff(self, ref='HEAD', ignore_space=False,
                   rename_detection=False):
        if self.object_type(ref) != 'commit':
            return False
        diff_data = self.cat(ref)
        diffs = {}
        diffs['parents'] = ' '.join(diff_data['parent'])
        diffs['author'] = diff_data['author']['name']
        diffs['email'] = email_normalizer(
            diffs['author'], diff_data['author']['email'])
        diffs['time'] = compute_relative_time(diff_data['author']['ts'])
        diffs['message'] = diff_data['message'].replace('\n', ' ')
        diffs['body'] = remove_unknown_character(diff_data['body'])
        parents = diffs['parents'].split(' ')
        if parents and parents[0]:
            diffs['difflist'] = self.get_3dot_diff(
                parents[0], ref, ignore_space=ignore_space,
                rename_detection=rename_detection)
        else:
            diffs['difflist'] = self._get_diff_for_first_commit(ref, parents)
        return diffs

    def _get_diff_for_first_commit(self, ref, parents):
        path = None
        sha1 = None
        sha2 = ref
        diffs_new = Diffs.from_diffs(
            self._gyt_repo.diff(sha1, sha2, path, parse_patch=True))
        return diffs_new

    def get_diff_tree(self, sha):
        c = self.cat(sha)
        if len(c['parent']) > 1:
            text = self.pygit2_repo.diff_tree(sha, from_ref=c['parent'][0])
        else:
            text = self.pygit2_repo.diff_tree(sha)
        return text

    def get_format_patch(self, sha):
        c = self.cat(sha)
        if len(c['parent']) > 1:
            text = self._gyt_repo.format_patch(c['parent'][0], sha)
        else:
            text = self._gyt_repo.format_patch_sha(sha)
        return text

    def get_all_tree(self, ref='HEAD'):
        return self._recurse_get_tree(ref, '')

    def _recurse_get_tree(self, ref, path):
        l = []
        for node in self._list_tree(ref, path):
            l.append(node)
            if node['type'] == 'tree':
                l.extend(self._recurse_get_tree(ref, node['path']))
        return l

    def _list_tree(self, ref, path):
        assert self.object_type(
            ref, path) == 'tree', "list_tree work on a tree"
        items = self.cat('%s:%s' % (ref, path))
        list_ = []
        for item in items:
            item_name = item['path'].decode('utf-8')
            item_path = '%s%s%s' % (path, '/' if path else '', item_name)
            # TODO check why we don't use os.path.join
            d = {
                'mode': item['mode'],
                'id': item['sha'],
                'type': item['type'],
                'name': item_name,
                'path': item_path,
            }
            if item['type'] == 'commit' and item['mode'] == '160000':
                url = self._get_submodule(ref).get(item_path, '')
                parsed_url = urlparse.urlparse(url)  # parse url into tuple
                if parsed_url.scheme == 'git':
                    url = urlparse.urlunparse(('http',) + parsed_url[1:])
                host = ''
                if parsed_url.netloc == 'code.dapps.douban.com':
                    host = 'code'
                elif parsed_url.netloc == 'github.com':
                    if parsed_url.path.startswith('/gist'):
                        host = 'gist'
                        d['x-gist-id'] = parsed_url.path.replace('/gist/', '')
                    else:
                        host = 'github'
                d['type'] = 'submodule'
                d['url'] = url
                d['host'] = host
            list_.append(d)
        return list_

    def list_files(self, ref):
        if not ref or ref not in self.get_branches():
            ref = 'HEAD'
        #filelist = self.call('ls-tree -r --name-only %s' % ref)
        filelist = self.pygit2_repo.ls_tree(
            ref, recursive=True, name_only=True)
        # return filelist.split('\n') if filelist else []
        return filelist

    def list_sha1_with_files(self, ref):
        if not ref or ref not in self.get_branches():
            ref = 'HEAD'
        list_tree = self._list_tree(ref, '')
        return [(item['id'], item['path']) for item in list_tree]

    def _get_submodule(self, ref):
        modules = self.pygit2_repo.show(
            '%s:%s' % (ref, '.gitmodules')).split('\n')
        if not modules:
            return modules
        from itertools import groupby
        modules = [list(group) for k, group in groupby(
            modules, lambda x: x.startswith('[submodule'))]
        modules = zip(*[modules[i::2] for i in range(0, 2)])
        _modules = []
        for a, b in modules:
            _modules.append((
                [c.split('=')[1].strip() for c in b if c.strip().startswith('path')][0],  # noqa
                [c.split('=')[1].strip().replace('.git', '')
                 for c in b if c.strip().startswith('url')][0]
            ))
        modules = dict(_modules)
        return modules

    def temp_branch_name(self):
        return 'patch_tmp' + time.strftime('%Y%m%d%H%M%S-') + \
            self._gyt_repo.sha()[10]

    def remove_temp_branch(self, tmp_branch):
        assert tmp_branch in self.get_branches(
        ), "Branch to be deleted must exist"
        assert tmp_branch.startswith('patch_tmp')
        last_reflog_msg = self._gyt_repo.reflog(tmp_branch)
        assert last_reflog_msg.split()[-1] == TEMP_BRANCH_MARKER, \
            "Branch %s not marked as temporary" % tmp_branch
        old_sha = self._gyt_repo.rev_parse(tmp_branch)
        self._gyt_repo.update_ref('refs/heads/%s' % tmp_branch,
                                  old_sha, delete=True)
        #self.call(['update-ref', '-d', 'refs/heads/%s' % tmp_branch, old_sha])

    def commit_one_file(self, filename, source, message, user, orig_hash='',
                        branch='master', parent='master'):
        # TODO Need to lock the repo!
        first = not bool(self._gyt_repo.rev_parse('HEAD', _raise=False))
        if first:
            assert branch == 'master', "can only commit to master when repo is empty"  # noqa
            assert parent == 'master', "can only commit to master when repo is empty"  # noqa
        else:
            assert parent in self.get_branches(
            ), "parent rev must exist if repo not empty"
        temp_new_branch = branch.startswith('patch_tmp')
        if temp_new_branch:
            reflog_msg = TEMP_BRANCH_MARKER
        else:
            reflog_msg = 'commit_one_file on %s' % branch
        assert ' ' not in branch, "Branch cannot have white spaces"
        source = source.replace('\r\n', '\n')
        tmp = tempfile.NamedTemporaryFile(mode='w', delete=False)
        tmp.write(source)
        tmp.close()
        self._gyt_repo.read_tree('HEAD', _raise=False)
        hash_obj = self._gyt_repo.hash_object(tmp.name)
        self._gyt_repo.update_index(hash_obj, filename,
                                    add=True,
                                    cacheinfo=True)
        tree_sha1 = self._gyt_repo.write_tree()
        env = make_git_env(user)
        if first:
            commit_sha1 = self._gyt_repo.commit_tree(
                tree_sha1, message, env=env)
        else:
            commit_sha1 = self._gyt_repo.commit_tree(
                tree_sha1, message, parent=parent, env=env)

        self._gyt_repo.update_ref('refs/heads/%s' % branch, commit_sha1,
                                  msg=reflog_msg, log=True)

        # clean temp file
        if os.path.isfile(tmp.name):
            os.remove(tmp.name)

    def commit_all_files(self, filenames, contents, oids, user, create=False,
                         default_filename_prefix='gistfile'):
        env = make_git_env(user, is_anonymous=not user)

        def _remove_file(self, sha1_with_files, sha1):
            oname = sha1_with_files[sha1]
            oname = _check_filename(oname)
            # self.call('update-index --add --remove --cacheinfo 100644 %s %s' %
            #          (oid, oname))
            self._gyt_repo.update_index(sha1, oname,
                                        add=True, remove=True,
                                        cacheinfo=True)
            #self.call('rm --cached %s' % oname)
            self._gyt_repo.rm(oname)

        def _check_filename(fn):
            for c in (' ', '<', '>', '|', ';', ':', '&', '`', "'"):
                fn = fn.replace(c, '\%s' % c)
            fn = fn.replace('/', '')
            return fn

        if create:
            sha1_with_files = {}
        else:
            sha1_with_files = dict(self.list_sha1_with_files('HEAD'))
        for index, (filename, content, oid) in enumerate(zip(
                filenames, contents, oids), start=1):
            if not filename and not content:
                continue
            if not filename:
                filename = default_filename_prefix + str(index)
            filename = _check_filename(filename)
            if oid and sha1_with_files.get(oid) != filename:
                _remove_file(self, sha1_with_files, oid)

            tmp_filename = tempfile.mktemp()
            filename = filename.decode('utf-8')
            with open(tmp_filename, 'w') as f:
                f.write(content.replace('\r\n', '\n'))
            #file_sha1 = self.call('hash-object -w %s' % tmp_filename)
            file_sha1 = self._gyt_repo.hash_object(tmp_filename)
            self._gyt_repo.update_index(
                file_sha1, filename, add=True, cacheinfo=True)
            # self.call('update-index --add --cacheinfo 100644 %s %s' %
            #          (file_sha1, filename))

        if not create:
            del_sha1s = set(sha1_with_files) - set(oids)
            for sha1 in del_sha1s:
                _remove_file(self, sha1_with_files, sha1)

        tree_sha1 = self._gyt_repo.write_tree()
        if create:
            commit_sha1 = self._gyt_repo.commit_tree(tree_sha1, ' ', env=env)
            # commit_sha1 = self.call(
            #    'commit-tree %s -m " "' % tree_sha1, _env=env)
        else:
            commit_sha1 = self._gyt_repo.commit_tree(
                tree_sha1, ' ', parent='master', env=env)
            # commit_sha1 = self.call(
            #    'commit-tree %s -p master -m " "' % tree_sha1, _env=env)
        # self.call(['-c', 'core.logAllRefUpdates=True',
        #          'update-ref', 'refs/heads/master', commit_sha1])
        self._gyt_repo.update_ref('refs/heads/master', commit_sha1, log=True)

    def rename_detection(self, ref1, ref2=''):
        repo = self._gyt_repo.repo
        ref1_cmt = repo.revparse_single(ref1)
        if not ref2:
            parent = ref1_cmt.parents
            if parent and parent[0]:
                ref2_cmt = parent[0]
            else:
                '''第一个commit'''
                diff = self._gyt_repo.diff(
                    None, ref1, rename_detection=True, patch=False)
                result = dict((d['new_filename'], d['filename'])
                              for d in diff if d['change'] == 'R100')
                return result
        else:
            ref2_cmt = repo.revparse_single(ref2)
        tree1 = ref1_cmt.tree
        tree2 = ref2_cmt.tree
        if ref2:
            diff = tree1.diff(tree2)
        else:
            diff = tree2.diff(tree1)
        diff.find_similar()
        result = dict((d.new_file_path, d.old_file_path)
                      for d in diff if int(d.similarity) > 80)
        return result

    def archive(self, name=''):
        name = name or self.project_name
        content = self._gyt_repo.archive(name, _raw=True)
        #content = self.call('archive --prefix=%s/ master' % name, _raw=True)
        outbuffer = StringIO()
        zipfile = gzip.GzipFile(mode='wb', compresslevel=6, fileobj=outbuffer)
        zipfile.writelines(content)
        zipfile.close()
        out = outbuffer.getvalue()
        return out

    def is_empty(self):
        return self._gyt_repo.is_empty()


class Commit(object):

    def __init__(self, repo_name, sha, tree=None, parent=None, author=None,
                 author_time=None, committer=None, commit_time=None,
                 message=None, shortlog=None):
        self.repo_name = repo_name
        self.sha = sha
        self.tree = tree
        self.parent = parent
        self.author = author
        self.time = self.author_time = author_time
        self.committer = committer
        self.commit_time = commit_time
        self.message = message
        if shortlog is None and message:
            shortlog = message.splitlines()[0]
        self.shortlog = shortlog
        self.message_body = ''.join(message.splitlines(True)[1:])

    def __eq__(self, y):
        return bool(y and isinstance(y, Commit) and (
            self.repo_name == y.repo_name and self.sha == y.sha))

    def __repr__(self):
        return "<Commit {sha} by {author} '{message}'>".format(
            sha=self.sha, author=self.author,
            message=self.message.encode('utf-8'))

    @property
    def url(self):
        return '/{proj}/commit/{sha}'.format(proj=self.repo_name,
                                             sha=self.sha)

    @property
    def shortsha(self):
        return self.sha[:7]

    def has_only_shortlog(self):
        return self.shortlog.strip() == self.message.strip()


class Diffs(list):

    @classmethod
    def from_diffs(cls, diffs):
        return cls(Diff.from_diff(diff) for diff in diffs)

    @property
    def n_additions(self):
        return sum(diff.n_additions for diff in self)

    @property
    def n_deletions(self):
        return sum(diff.n_deletions for diff in self)


class Diff(object):

    def __repr__(self):
        return "Diff({path}, {old}, {new})".format(
            path=repr(self.filepath), old=self.old_sha, new=self.new_sha)

    def __init__(self, filepath, old_sha=None, new_sha=None, chunks=None,
                 generated=False, binary=False, status=None,
                 new_filepath=None):
        self.filepath = filepath
        self.old_sha = old_sha
        self.new_sha = new_sha
        self.chunks = chunks
        self.generated = generated
        self.binary = binary
        self.status = status
        self.new_filepath = new_filepath

    @classmethod
    def from_diff(cls, diff):
        filepath = diff['filename']
        old_sha = diff['asha'][:7]
        new_sha = diff['bsha'][:7]
        if old_sha == '0000000':
            old_sha = None
        if new_sha == '0000000':
            new_sha = None
        generated = diff['generated']
        binary = diff['binary']
        ignore = generated or binary
        chunks = [DiffChunk.chunk_from_gyt_diff(patch, ignore)
                  for patch in diff['patch']]
        status = diff['change']
        new_filepath = diff['new_filename']
        return cls(filepath, old_sha, new_sha, chunks, generated, binary,
                   status, new_filepath)

    @property
    def type(self):
        if self.status == 'R':
            return 'renamed'
        if self.old_sha:
            if self.new_sha:
                return 'modified'
            else:
                return 'removed'
        else:
            return 'added'

    @property
    def n_additions(self):
        return sum(chunk.chunk_n_additions() for chunk in self.chunks)

    @property
    def n_deletions(self):
        return sum(chunk.chunk_n_deletions() for chunk in self.chunks)

    @property
    def diff_content(self):
        return [l for c in self.chunks for l in c.diff_lines_with_num()]

    @property
    def side_diff_content(self):
        return [l for c in self.chunks for l in c.side_lines()]

    def smart_slice(self, num):
        content = self.diff_content[:num + 1]
        if len(content) < 15:
            return content
        else:
            tip_pos = 0
            for idx, (type, old, new, line) in enumerate(content):
                if old.strip() == '...':
                    tip_pos = idx
            content = content[tip_pos:]
            if len(content) > 25:
                return content[-25:]
            else:
                return content


class DiffChunk(object):
    TIP_LINE_RE = re.compile(
        r'^@@+ -(?P<old_line_no>\d+),?(?P<old_n_lines>\d+)? '
        '(?:-\d+,\d+ )?'
        '\+(?P<new_line_no>\d+),?(?P<new_n_lines>\d+)? @@+')

    def __init__(self, tip_line, diff_lines, ignore):
        self.tip_line = tip_line
        self.reallines = diff_lines
        if not ignore and len(diff_lines) < RE_HUNK_LIMIT:
            self.diff_lines = rehunk(diff_lines)
        else:
            self.diff_lines = diff_lines

    @classmethod
    def chunk_from_gyt_diff(cls, chunk, ignore=False):
        tip_line, diff_lines = chunk
        return cls(tip_line, diff_lines, ignore)

    def diff_lines_with_num(self):
        old, new = self._start_line_numbers()
        below_l, below_r = old, new
        result = []
        result.append(('tips', '...', '...', self.tip_line))
        for type_, l in self.diff_lines:
            if type_ == 'rem':
                result.append(('deletion', str(old), ' ', l))
                old += 1
            elif type_ == 'add':
                result.append(('insertion', ' ', str(new), l))
                new += 1
            else:
                result.append(('normal', str(old), str(new), l))
                old += 1
                new += 1
        above_l, above_r = old - 1, new - 1
        result[0] = ('tips', '...', '...',
                     self.tip_line + '||%s,%s,%s,%s' % (
                         below_l, below_r,
                         above_l, above_r)
                     )
        return result

    def side_lines(self):
        old, new = self._start_line_numbers()
        result = []
        result.append((
            '...', 'normal', self.tip_line, '...', 'normal', self.tip_line))
        type_ = {'emp': 'normal', 'normal': 'normal', 'add': 'insertion',
                 'rem': 'deletion'}
        for l, r in rehunk(self.reallines, True):  # side hunk
            l_type = l[1]
            r_type = r[1]
            disp_old = str(old) if l_type != 'emp' else ' '
            disp_new = str(new) if r_type != 'emp' else ' '
            result.append((disp_old, type_.get(l_type), l[2], disp_new,
                           type_.get(r_type), r[2]))
            if l_type != 'emp':
                old += 1
            if r_type != 'emp':
                new += 1
        return result

    def _start_line_numbers(self):
        m = self.TIP_LINE_RE.match(self.tip_line)
        old_line_no = m.group('old_line_no')
        new_line_no = m.group('new_line_no')
        return int(old_line_no), int(new_line_no)

    def chunk_n_additions(self):
        return len([line for line in self.diff_lines if line[0] == 'add'])

    def chunk_n_deletions(self):
        return len([line for line in self.diff_lines if line[0] == 'rem'])


def make_git_env(user=None, is_anonymous=False):
    env = {}
    if is_anonymous:
        env['GIT_AUTHOR_NAME'] = 'anonymous'
        env['GIT_AUTHOR_EMAIL'] = 'anonymous@douban.com'
        env['GIT_COMMITTER_NAME'] = 'anonymous'
        env['GIT_COMMITTER_EMAIL'] = 'anonymous@douban.com'
    else:
        env['GIT_AUTHOR_NAME'] = user.username
        env['GIT_AUTHOR_EMAIL'] = user.email
        env['GIT_COMMITTER_NAME'] = user.username
        env['GIT_COMMITTER_EMAIL'] = user.email
    return env
