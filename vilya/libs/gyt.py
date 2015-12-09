# coding=utf-8

import os
import shlex
import re
import subprocess
import logging
import collections
from os.path import splitext
from pygit2 import (
    GIT_OBJ_COMMIT, GIT_OBJ_TREE,
    GIT_OBJ_BLOB, GIT_OBJ_TAG,
    GIT_SORT_TIME, GIT_DIFF_IGNORE_WHITESPACE
)

from vilya.libs.git2 import Git2
from vilya.libs.generated import Generated
from vilya.libs.consts import IS_GENERATED, NOT_GENERATED, IGNORE_FILE_EXTS, MINIFIED

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

GIT_EXECUTABLE = 'git'
GIT_DIR_DEFAULT = '.git'
GIT_MIN_VERSION = '1.7.10'
HEADER = re.compile(r"""^diff[ ]--git[ ]a/(?P<a_path>.+)[ ]b/(?P<b_path>.+)""")

# plumbing git command:
# apply checkout-index commit-tree hash-object index-pack merge-file merge-index mktag mktree pack-objects
# prune-packed read-tree symbolic-ref unpack-objects update-index update-ref write-tree cat-file diff-files
# diff-index diff-tree for-each-ref ls-files ls-remote ls-tree merge-base name-rev pack-redundant rev-list
# show-index show-ref tar-tree unpack-file var verify-pack daemon fetch-pack http-backend send-pack
# update-server-info http-fetch http-push parse-remote receive-pack shell upload-archive upload-pack
# check-attr check-ref-format fmt-merge-msg mailinfo mailsplit merge-one-file patch-id peek-remote sh-setup
# stripspace
#
# porcelain git commands:
# add am archive bisect branch bundle checkout cherry-pick citool clean clone commit describe diff fetch format-patch
# gc grep gui init log merge mv notes pull push rebase reset revert rm shortlog show stash status submodule tag config
# fast-export fast-import filter-branch lost-found mergetool pack-refs prune reflog relink remote repack replace repo-config
# annotate blame cherry count-objects difftool fsck get-tar-commit-id help instaweb merge-tree rerere rev-parse show-branch
# verify-tag whatchanged archimport cvsexportcommit cvsimport cvsserver
# imap-send quiltimport request-pull send-email svn

isa = isinstance

OBJ_TYPE = {
    GIT_OBJ_COMMIT: 'commit',
    GIT_OBJ_BLOB: 'blob',
    GIT_OBJ_TREE: 'tree',
    GIT_OBJ_TAG: 'tag',
}


class GytError(Exception):
    pass


class GytRepoNotInited(GytError):
    pass


def shlex_split_utf8(cmd):
    # shlex don't accept unicode if python < 2.7.3
    if isa(cmd, basestring):
        cmd = [s.decode('utf-8') for s in shlex.split(cmd.encode('utf-8'))]
    elif not isa(cmd, collections.Iterable):
        cmd = [cmd]
    return cmd


class _Repo(object):
    def __init__(self, path, work_tree=None, bare=None):
        git_dir, work_tree, bare = _massage_params(path, work_tree, bare)
        assert is_git_dir(git_dir), "%s must be a git dir" % git_dir
        self.git_dir = git_dir
        self.work_tree = work_tree
        self.repo = Git2(self.git_dir)

    def __repr__(self):
        return "_Repo('%s'%s)" % (self.git_dir,
                                  ", '%s'" % self.work_tree if self.work_tree else '')

    def call(self, cmd, _env=None, _raise=True, _raw=False):
        cmd = shlex_split_utf8(cmd)
        add2cmd = ['--git-dir', self.git_dir]
        if self.work_tree:
            add2cmd += ['--work-tree', self.work_tree]
        return call([GIT_EXECUTABLE] + add2cmd + cmd, _env=_env, _raise=_raise, _raw=_raw)

    def is_bare(self):
        return not bool(self.work_tree)

    # FIXME: use pygit2
    def is_empty(self):
        is_empty = False
        try:
            self.repo.revparse_single('HEAD')
        except KeyError:
            is_empty = True
        return is_empty

    def head(self, short=False):
        head = self.repo.lookup_reference('HEAD').target
        if head and short and head.startswith('refs/'):
            head = re.sub('^refs/[^/]*/', '', head)
        return head or None

    def sha(self, rev='HEAD'):
        if not rev:
            return None
        try:
            sha = self.repo.revparse_single(rev)
        except KeyError:
            return None
        except ValueError:
            return None
        return sha.hex

    def cat(self, sha, only_type=False):
        sha = self.sha(sha)
        if not sha:
            return False
        obj = self.repo.revparse_single(sha)
        objtype = obj.type
        if only_type:
            return OBJ_TYPE.get(objtype)
        if objtype == GIT_OBJ_COMMIT:
            return self.cat_commit(sha, obj)
        elif objtype == GIT_OBJ_TAG:
            return self.cat_tag(sha, obj)
        elif objtype == GIT_OBJ_TREE:
            return self.cat_tree(sha, obj)
        elif objtype == GIT_OBJ_BLOB:
            return self.cat_blob(sha, obj)
        else:
            raise NotImplementedError("Object type %s unknown" % objtype)

    def cat_commit(self, sha, obj):
        return self.repo.cat_commit(sha, obj)

    def cat_tag(self, sha, obj):
        return self.repo.cat_tag(sha, obj)

    def cat_tree(self, sha, obj):
        return self.repo.cat_tree(sha, obj)

    def cat_blob(self, sha, obj):
        return self.repo.cat_blob(sha, obj)

    def remotes(self):
        return self.repo.remotes

    def add_remote(self, name, url):
        if name not in [r.name for r in self.remotes()]:
            self.repo.create_remote(name, url)

    def add_remote_hub(self, name, url):
        self.add_remote('hub/%s' % name, url)

    def fetch_all(self):
        self.repo.fetch()
        #self.call('fetch --all')

    def fetch_mirror(self, _env=None):
        self.call('fetch -q', _env=_env)

    def diff_tree(self, from_ref, to_ref):
        text = self.call('diff-tree -p %s %s' % (from_ref, to_ref), _raw=True)
        return text

    def format_patch(self, from_ref, to_ref):
        text = self.call(
            'format-patch --stdout %s...%s' % (from_ref, to_ref))
        return text

    def format_patch_sha(self, to_ref):
        text = self.call(
            'format-patch -1 --stdout %s' % to_ref)
        return text

    def diff_numstat(self, from_ref, to_ref):
        output = self.call('diff --numstat %s...%s' %
                           (from_ref, to_ref))
        return output

    def merge(self, ref, msg='automerge', commit_msg='', no_ff=False, _raise=True, _env=None):
        cmd = ['merge', ref]
        if msg:
            cmd.append('-m')
            cmd.append(msg)
        if commit_msg:
            cmd.append('-m')
            cmd.append(commit_msg)
        if no_ff:
            cmd.append('--no-ff')
        errcode = self.call(cmd, _raise=_raise, _env=_env)
        return errcode

    def push(self, remote, ref):
        self.call(['push', remote, ref])

    def blame(self, ref, path):
        res = self.call('blame -p -CM %s -- %s' % (ref, path))
        return res

    def blame_line(self, ref, path, lineno):
        res = self.call('blame -L %s,%s --porcelain %s -- %s' % (
            lineno, lineno, ref, path))
        return res

    def refs(self, select='all', short=False, current_first=False):
        """List selected refs, either `branches` or `tags` or `all`"""
        selects = {
            'all': 'refs/',
            'branches': 'refs/heads',
            'tags': 'refs/tags',
        }
        assert select in selects, "select must be 'all' (default), 'branches' or 'tags'"
        fmt = ['refname:short' if short else 'refname']
        key = 'shortname' if short else 'name'
        refs = []
        refs_dict = self.repo.for_each_ref(pattern=selects[select], format=fmt)
        for ref in refs_dict:
            refs.append(ref[key].decode('utf-8'))
        if current_first:
            self._move_current_in_first(refs, short)
        return refs

    def ref_details(self, ref):
        refs = self.repo.get_ref(ref)
        return refs if refs else None

    def _move_current_in_first(self, refs, short):
        cur = self.head(short)
        if cur in refs:
            refs.remove(cur)
            refs.insert(0, cur)

    # FIXME: remove this.
    def update_ref(self, ref, newvalue, msg='', delete=False, log=False):
        if log:
            cmd = ['-c', 'core.logAllRefUpdates=True', 'update-ref']
            if msg:
                cmd.append('-m')
                cmd.append('%s' % msg)
            cmd.append(ref)
            cmd.append(newvalue)
            return self.call(cmd)
        if delete:
            self.call(['update-ref', '-d', ref, newvalue])
            #self.call(['update-ref', '-d', 'refs/heads/%s' % tmp_branch, old_sha])
            return
        return self.repo.update_ref(ref, newvalue, delete)

    # FIXME: remove this.
    def rev_list(self, to_ref, from_ref=None,
                 paths=None, skip=0, max_count=0,
                 author=None, query=None):
        return self.repo.rev_list(to_ref, from_ref, paths, skip, max_count,
                                  author, query)

    def rev_walk_shas(self, start, end):
        if self.is_empty():
            return []

        if not end:
            return []

        try:
            ender = self.repo.revparse_single(end)
        except KeyError:
            return []

        walker = self.repo.walk(ender.id, GIT_SORT_TIME)

        if start:
            try:
                starter = self.repo.revparse_single(start)
                walker.hide(starter.id)
            except KeyError:
                starter = None

        out = [x.hex for x in walker]
        return out

    def logs(self, from_ref=None, to_ref='HEAD', path=None):
        try:
            lines = self.rev_list(to_ref, from_ref, paths=path)
        except KeyError:
            return []
        return [self.cat(sha.hex) for sha in lines]

    def config(self, key=None):
        # TODO set conf value
        conf = dict(c.split('\n', 1)
                    for c in self.call('config --list --null').split('\0') if c)
        return conf.get(key) if key else conf

    def clone(self, to_path, bare=True, branch=None, mirror=None):
        clone(self.git_dir, to_path, bare=bare, branch=branch, mirror=mirror)
        return repo(to_path, bare=bare)

    def reflog(self, branch):
        return self.call(['reflog', '-n1', branch])

    def rev_parse(self, ref, _raise=True):
        return self.call(['rev-parse', ref], _raise=_raise)

    def archive(self, name, _raw=False):
        return self.call('archive --prefix=%s/ master' % name, _raw=_raw)

    def update_index(self, sha, name, add=False, remove=False, cacheinfo=False):
        cmd = ['update-index']
        if add:
            cmd.append('--add')
        if remove:
            cmd.append('--remove')
        if cacheinfo:
            cmd.append('--cacheinfo')
        cmd.append('100644')
        cmd.append(sha)
        cmd.append(name)
        self.call(cmd)

    def hash_object(self, name):
        return self.call(['hash-object', '-w', name])

    def write_tree(self):
        return self.call('write-tree')

    def commit_tree(self, sha, msg, parent=None, env=None):
        cmd = ['commit-tree', sha]
        if parent:
            cmd.append('-p')
            cmd.append(parent)
        if msg:
            cmd.append('-m')
            cmd.append('%s' % msg)
        return self.call(cmd, _env=env)

    def read_tree(self, ref, _raise=True):
        self.call(['read-tree', ref], _raise=_raise)

    def rm(self, name):
        self.call(['rm', '--cached', name])

    def make_diff_params(self, from_ref, to_ref, path, patch, rename_detection, ignore_space):
        joiner = '%s..%s' if path else '%s...%s'  # TODO explain this
        to_sha = self.sha(to_ref)
        if from_ref:
            from_sha = self.sha(from_ref)
        else:
            parents = self.cat(to_sha)['parent']
            if parents:
                from_sha = parents[0]
            else:
                # Special case of very first commit: no parent
                from_sha = None
        params = ['--raw', '-z']
        if patch:
            params += ['--patch']
        if rename_detection:
            params += ['--find-renames']
        if ignore_space:
            params += ['-w']
        if from_sha:
            cmd = ['diff'] + params + [joiner % (from_sha, to_sha)]
        else:
            cmd = ['log', "--pretty=format:",
                   '--no-abbrev-commit'] + params + [to_sha]
        if path:
            cmd += ['--', path]
        return cmd, from_sha, to_sha

    def diff_file_type(self, changes, patches, from_sha, to_sha):
        for i in xrange(len(changes)):
            changes[i]['patch'] = patches[i]
            name = changes[i]['filename']
            ext_name = splitext(name)[1]
            changes[i]['binary'] = False
            if ext_name in NOT_GENERATED:
                if name.endswith(MINIFIED):
                    changes[i]['generated'] = True
                else:
                    changes[i]['generated'] = False
            elif ext_name in IS_GENERATED:
                changes[i]['generated'] = True
            elif ext_name in IGNORE_FILE_EXTS:
                changes[i]['binary'] = True
                changes[i]['generated'] = False
            else:
                if changes[i]['change'] in ['D', 'C', 'R', 'T']:
                    cat_ref = from_sha
                else:
                    cat_ref = to_sha

                def _get_data():
                    try:
                        data = self.cat('%s:%s' % (
                            cat_ref, name))
                    except:  # very first commit ??
                        data = ''
                    return data
                changes[i]['generated'] = Generated.is_generated(
                    name, _get_data)
        return changes

    def diff(self, from_ref=None, to_ref='HEAD', path=None, patch=True,
             parse_patch=True, rename_detection=False, ignore_space=False,
             context_lines=3, paths=None):
        cmd, from_sha, to_sha = self.make_diff_params(from_ref, to_ref,
                                                      path, patch,
                                                      rename_detection,
                                                      ignore_space)
        if not to_sha:
            return []
        if from_sha:
            ref_cmt1 = self.repo.revparse_single(from_sha)
            ref_cmt2 = self.repo.revparse_single(to_sha)
            opt = 0
            if ignore_space:
                opt += GIT_DIFF_IGNORE_WHITESPACE
            kwargs = {'context_lines': context_lines}
            if path:
                kwargs.update({'paths': [path]})
            if paths:
                kwargs.update({'paths': paths})
            diff = ref_cmt1.tree.diff(ref_cmt2.tree, opt, **kwargs)
            if rename_detection:
                diff.find_similar()
            changes = parse_pygit_diff_head(diff)
            ps = [p for p in diff]
            if not ps:
                return []
            if patch:
                patches, filenames = parse_raw_diff_patches(
                    diff.patch, parse_patch)
                changes = self.diff_file_type(
                    changes, patches, from_sha, to_sha)
        else:
            full_stream = self.call(cmd)
            head, _, patches_stream = full_stream.partition('\0\0')
            changes = parse_raw_diff_head(head)
            if patch:
                patches, filenames = parse_raw_diff_patches(
                    patches_stream, parse_patch)
                changes = self.diff_file_type(
                    changes, patches, from_sha, to_sha)
        return changes


def repo(path, work_tree=None, bare=None, init=False, _raise=True):
    git_dir, work_tree, bare = _massage_params(path, work_tree, bare)
    if not os.path.exists(git_dir):
        os.makedirs(git_dir)
    if init:
        assert not is_git_dir(git_dir), "Cannot re-init a git dir"
        if bare:
            call(GIT_EXECUTABLE, '--git-dir', git_dir, 'init', '--bare')
        else:
            call(GIT_EXECUTABLE, '--git-dir',
                 git_dir, '--work-tree', work_tree, 'init')
    if not is_git_dir(git_dir):
        if _raise:
            raise GytRepoNotInited("%s is not a git dir" % git_dir)
        else:
            return None
    return _Repo(git_dir, work_tree, bare)


def is_git_dir(path):
    # This is memoized, should work if dirs are made git-dirs with git init.
    # The memoization will break things if we manually make a git-dir become a non-git-dir
    # Which I hope we don't!
    if not is_git_dir._memoize.get(path, False):
        is_ = Git2.is_git_dir(path)
        is_git_dir._memoize[path] = is_
    return is_git_dir._memoize[path]

is_git_dir._memoize = {}


def clear_memoizer():
    # Used in unit tests
    is_git_dir._memoize = {}


def clone(url, path, bare=False, branch=None, mirror=None, _env=None):
    cmd = [GIT_EXECUTABLE, 'clone']
    if branch:
        cmd.append('-b')
        cmd.append(branch)
    if bare:
        cmd.append('--bare')
    if mirror:
        cmd.append('--mirror')
    cmd.append(url)
    cmd.append(path)
    call(cmd, _env=_env)
    # FIXME: dog slow
    #Git2.clone(url, path, bare=bare, branch=branch)
    if bare:
        call([GIT_EXECUTABLE, '--git-dir', path, 'update-server-info'])


def call(*args, **kwargs):
    """System calls with string or list args"""
    _raise = kwargs.pop('_raise', True)
    _raw = kwargs.pop('_raw', False)
    _env = kwargs.pop('_env', {})
    assert not kwargs, "call kwargs not understood in %s" % kwargs
    fullcmd = []
    if len(args) == 1:
        cmd = args[0]
    else:
        cmd = args
    cmd = shlex_split_utf8(cmd)
    # flatten
    fullcmd = []
    for el in cmd:
        if isa(el, basestring):
            fullcmd.append(el)
        elif isa(el, collections.Iterable):
            fullcmd.extend(el)
        else:
            fullcmd.append(str(el))
    assert len(fullcmd) >= 1, "Need to pass at least a command"
    try:
        process = subprocess.Popen(fullcmd, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, env=_env)
    except (OSError, TypeError) as err:
        logger.error("Unable to open process %s" % fullcmd)
        raise err
    out, err = process.communicate()
    out = str(out)
    err = str(err)
    # logger.debug("## Returned %s from call %s" % (process.returncode, ' '.join(fullcmd)))
    # logger.debug("## Stdout:\n%r" % out)
    # logger.debug("## Stderr:\n%r" % err)
    if process.returncode == 0:
        if _raw:
            return out
        else:
            return unicode(out.strip().decode('utf-8', 'ignore'))
    else:
        if _raise:
            raise GytError(fullcmd, process.returncode, err.strip())
        else:
            return False


def _massage_params(path, work_tree, bare):
    assert not (work_tree and bare is True), "Bare repos cannot have work tree"
    if bare is False and not work_tree:
        git_dir = os.path.join(path, GIT_DIR_DEFAULT)
        work_tree = path
        bare = False
    elif work_tree:
        git_dir = path
        work_tree = work_tree
        bare = False
    else:
        git_dir = path
        work_tree = work_tree
        bare = True
    return git_dir, work_tree, bare


def parse_raw_diff_head(stream):
    i0 = 0
    changes = []
    while True:
        i1 = stream.find('\0', i0 + 1)
        if i1 == -1:
            break
        # TODO will break in case of git mv
        amode, bmode, asha, bsha, change = stream[i0 + 1:i1].split(' ')
        i0 = stream.find('\0', i1 + 1)
        if i0 == -1:
            i0 = len(stream)
        filename = stream[i1 + 1:i0]
        if change[0] in ['C', 'R']:
            i2 = stream.find('\0', i0 + 1)
            if i2 == -1:
                i2 = len(stream)
            new_filename = stream[i0 + 1:i2]
            i0 = i2
        elif change[0] == 'T':
            changes.append({'amode': amode,
                            'bmode': '',
                            'asha': asha,
                            'bsha': '',
                            'change': change,
                            'filename': filename,
                            'new_filename': filename})
            changes.append({'amode': '',
                            'bmode': bmode,
                            'asha': '',
                            'bsha': bsha,
                            'change': change,
                            'filename': filename,
                            'new_filename': filename})
            continue
        else:
            new_filename = ''
        changes.append({
            'amode': amode,
            'bmode': bmode,
            'asha': asha,
            'bsha': bsha,
            'change': change,
            'filename': filename,
            'new_filename': new_filename,
            #'patch': self._diff_patch(asha, bsha, change, parse_patch),
        })
    return changes


def parse_raw_diff_patches(patches, parse_patch):
    res = []
    filenames = set()
    cur_patch_idx = -1
    cur_chunk_idx = -1
    type_ = {' ': 'idem', '+': 'add', '-': 'rem', '\\': 'other'}
    for line in patches.splitlines():
        if line == '':
            # see http://onimaru-beta.intra.douban.com/code/group/78925/
            # Could be a problem with windows ^M
            continue
        if line.startswith('diff'):
            match = re.match(HEADER, line)
            if match:
                a = match.group('a_path')
                b = match.group('b_path')
                filenames.add(a)
                filenames.add(b)
            cur_patch_idx += 1
            cur_chunk_idx = -1
            res.append([])
            continue
        if line.startswith('@@'):
            cur_chunk_idx += 1
            res[cur_patch_idx].append((line, []))
            continue
        if cur_chunk_idx < 0 or cur_patch_idx < 0:
            continue  # Lines before the real patch part
        cur_chunk = res[cur_patch_idx][cur_chunk_idx][1]
        if parse_patch:
            cur_chunk.append((type_.get(line[0], 'ERR'), line[1:]))
        else:
            cur_chunk.append(line)
    return res, filenames


def parse_pygit_diff_head(diff):
    changes = []
    for patch in diff:
        changes.append({
            'amode': '100644',
            'bmode': '100644',
            'asha': patch.old_oid,
            'bsha': patch.new_oid,
            'change': patch.status,
            'filename': patch.old_file_path,
            'new_filename': patch.new_file_path,
        })
    return changes


def update_hook(hook_dir, link=False):
    subprocess.check_call(['rm', '-r', hook_dir])
    if link:
        subprocess.check_call(['ln', '-s', '/var/dae/apps/code/hub/hooks',
                               hook_dir])
