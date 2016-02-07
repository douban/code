# -*- coding: utf-8 -*-
import os
from datetime import datetime
from pygit2 import (
    Repository,
    clone_repository, init_repository,
    GIT_OBJ_COMMIT, GIT_OBJ_TREE,
    GIT_OBJ_BLOB, GIT_OBJ_TAG,
    GIT_REF_OID, GIT_REF_SYMBOLIC,
    GIT_SORT_TIME, GIT_SORT_REVERSE,
    GIT_DIFF_REVERSE,
)
from pytz import FixedOffset


PYGIT2_OBJ_TYPE = {
    GIT_OBJ_COMMIT: 'commit',
    GIT_OBJ_BLOB: 'blob',
    GIT_OBJ_TREE: 'tree',
    GIT_OBJ_TAG: 'tag',
}


def format_pygit2_signature(signature):
    d = {}
    d['date'] = datetime.fromtimestamp(
        signature.time,
        # FIXME: add offset for app.
        # FixedOffset(signature.offset, None)
    )
    d['name'] = signature.name
    d['email'] = signature.email
    # strftime('%Y-%m-%dT%H:%M:%S+0800')
    d['ts'] = str(signature.time)
    d['tz'] = datetime.fromtimestamp(signature.time,
                                     FixedOffset(signature.offset)
                                     ).strftime('%z')
    return d


def foreach_pygit2_config(key, name, lst):
    lst[key] = name
    return 0


def format_pygit2_object_type(type):
    if type in PYGIT2_OBJ_TYPE:
        return PYGIT2_OBJ_TYPE[type]
    return ''


def format_short_reference_name(name):
    short = ''
    if name.startswith('refs/heads/'):
        short = name[11:]
    elif name.startswith('refs/remotes/'):
        short = name[13:]
    elif name.startswith('refs/tags/'):
        short = name[10:]
    elif name.startswith('refs/'):
        short = name[5:]
    else:
        return name
    return short


def complete_reference_name(name):
    if name.startswith('refs/'):
        return name
    prefixs = ['refs/heads/', 'refs/remotes/', 'refs/tags/', 'refs/']
    refs = ['%s%s' % (p, name) for p in prefixs]
    return refs


# FIXME: dog slow
# DO NOT USE THIS
def clone(url, path, bare=False, branch=None):
    url = url[:-1] if url.endswith('/') else url
    repo = clone_repository(url, path, bare=bare, checkout_branch=branch)
    # update-server-info if bare
    return repo


class Git2(Repository):

    # support: <ref> <newvalue>, -d <ref> <newvalue>
    # FIXME: args 'delete' is not tested.
    def update_ref(self, ref, newvalue, delete=False):
        if self.is_empty:
            return False
        if delete:
            repo_ref = self.lookup_reference(ref)
            target = repo_ref.target
            if repo_ref.type == GIT_REF_OID:
                commit = self.revparse_single(newvalue)
                if target.hex == commit.hex:
                    repo_ref.delete()
                    return True
            elif repo_ref.type == GIT_REF_SYMBOLIC:
                if target == newvalue:
                    repo_ref.delete()
                    return True
            return False

        try:
            commit = self.revparse_single(newvalue)
        except KeyError:
            return False

        try:
            repo_ref = self.lookup_reference(ref)
        except KeyError:
            self.create_reference(ref, commit.hex)
            return True

        try:
            if repo_ref.type == GIT_REF_OID:
                if commit.type == GIT_OBJ_COMMIT:
                    repo_ref.target = commit.hex
            elif repo_ref.type == GIT_REF_SYMBOLIC:
                repo_new = self.lookup_reference(newvalue)
                repo_ref.target = repo_new.name
        except OSError:
            return False

        return True

    # support: -- paths, --max-count, --skip, --author
    def rev_list(self, to_ref, from_ref=None,
                 paths=None, skip=0, max_count=0,
                 author=None, query=None):
        if self.is_empty:
            return []
        if not to_ref:
            return []
        commits_index_list = []
        commits_dict = {}
        to_commit = self.revparse_single(to_ref)
        if to_commit.type == GIT_OBJ_TAG:
            to_commit = self[to_commit.target]
        walker = self.walk(to_commit.oid, GIT_SORT_TIME)
        if from_ref:
            try:
                from_commit = self.revparse_single(from_ref)
                if from_commit.type == GIT_OBJ_TAG:
                    from_commit = self[from_commit.target]
                walker.hide(from_commit.oid)
            except KeyError:
                from_commit = None

        def check_query(commit, query):
            if query and query in commit.message:
                return True
            elif not query:
                return True

        def check_author(commit, author):
            if author and commit.author.name == author:
                return True
            elif author and commit.author.email == author:
                return True
            elif not author:
                return True

        def check_paths(tree, paths):
            try:
                entry = tree[paths]
            except KeyError:
                return None
            return entry

        # FIXME: add quick diff
        def check_file_change(commit, paths):
            commit_tree = commit.tree
            parents = commit.parents
            if paths and check_paths(commit_tree, paths):
                count = 0
                c_entry = commit_tree[paths]
                for p in parents:
                    parent_tree = p.tree
                    if commit_tree.id == parent_tree.id:
                        return False
                    p_entry = check_paths(parent_tree, paths)
                    if not p_entry:
                        count += 1
                        continue
                    if p_entry.id != c_entry.id:
                        count += 1
                if count == len(parents):
                    return True
            elif not paths:
                return True

        if max_count:
            length = max_count + skip if skip else max_count
        else:
            length = 0
        for c in walker:
            if all([check_author(c, author),
                    check_file_change(c, paths),
                    check_query(c, query)]):
                index = c.hex
                if index not in commits_index_list:
                    commits_index_list.append(index)
                commits_dict[index] = c
            if length and len(commits_index_list) > length:
                break
        if skip:
            commits_index_list = commits_index_list[skip:]
        return [commits_dict[i] for i in commits_index_list]

    def for_each_ref(self, pattern='', format=[]):
        """ support format: refname, objectname, objecttype, tree """
        rs = []
        refs = self.listall_references()
        if pattern:
            if pattern in refs:
                refs = [pattern]
            else:
                refs = [r for r in refs
                        if r.startswith(pattern)
                        and (len(r) > len(pattern)
                             and (r[len(pattern) - 1] == '/'
                                  or r[len(pattern)] == '/'))]
        else:
            refs = list(refs)
        refs.sort()
        for ref in refs:
            r = {}
            ref_obj = self.lookup_reference(ref)
            target = self[ref_obj.target]
            if not format or 'objectname' in format:
                r['sha'] = target.hex
            if not format or 'objecttype' in format:
                r['type'] = format_pygit2_object_type(target.type)
            if not format or 'tree' in format:
                r['tree'] = target.tree.hex
            if not format or 'refname:short' in format:
                r['shortname'] = format_short_reference_name(ref)
            if not format or 'refname' in format:
                r['name'] = ref
            rs.append(r)
        return rs

    # FIXME
    def show(self, reference, path=None):
        try:
            obj = self.revparse_single(reference)
            if obj.type == GIT_OBJ_BLOB:
                return obj.data
        except KeyError:
            pass
        return ''

    # FIXME: dog slow
    # DO NOT USE THIS
    def clone(self, url, path, bare=False, branch=None):
        #url = self.path[:-1] if self.path.endswith('/') else self.path
        url = url[:-1] if url.endswith('/') else url
        repo = clone_repository(url, path, bare=bare, checkout_branch=branch)
        # update-server-info if bare
        return repo

    def init(self, bare=None):
        repo = init_repository(self.path, bare=bare)
        return repo

    # FIXME
    def fetch(self):
        for remote in self.remotes:
            remote.fetch()

    def update_server_info(self):
        return

    def update_info_refs(self):
        return

    def update_info_packs(self):
        return

    # FIXME
    def add_remote(self, name, url):
        self.create_remote(name, url)

    # FIXME
    def ref_log(self):
        head = self.lookup_reference('refs/heads/master')
        for entry in head.log():
            print(entry.message)

    def log(self, reference='HEAD', from_ref=None, shortstat=None,
            no_merges=None, reverse=None):
        sha = self._resolve_version(reference)

        sort = GIT_SORT_TIME
        if reverse is True:
            sort |= GIT_SORT_REVERSE

        commits = []
        walker = self.walk(sha, sort)
        if from_ref:
            from_sha = self._resolve_version(from_ref)
            if not from_sha:
                return commits
            walker.hide(from_sha)

        for commit in walker:
            _commit = {}
            if no_merges:
                parents = commit.parents
                if parents and len(parents) > 1:
                    continue

            if shortstat:
                parents = commit.parents
                if len(parents) == 0:
                    opt = GIT_DIFF_REVERSE
                    diff = commit.tree.diff(flags=opt, empty_tree=True)
                else:
                    parent = parents[0]
                    diff = parent.tree.diff(commit.tree)
                patches = [p for p in diff]
                additions = 0
                deletions = 0
                changed_files = len(patches)
                for p in patches:
                    additions += p.additions
                    deletions += p.deletions
                _commit['additions'] = additions
                _commit['deletions'] = deletions
                _commit['files'] = changed_files

            _commit['sha'] = commit.hex
            _commit['author_time'] = commit.author.time
            _commit['committer_time'] = commit.committer.time
            _commit['author_name'] = commit.author.name
            _commit['author_email'] = commit.author.email
            commits.append(_commit)
        return commits

    def hash_object(self, path, type='blob'):
        oid = self.create_blob_fromdisk(path)
        hex = self[oid].hex
        return hex

    def update_index(self, path):
        self.index.add(path)

    def rm_cache(self, path):
        self.index.remove(path)

    def read_tree(self, path):
        self.index.read_tree()

    def write_tree(self):
        self.index.write_tree()

    def diff_tree(self, to_ref, from_ref=None):
        to_sha = self._resolve_version(to_ref)
        to_commit = self[to_sha]
        if from_ref:
            from_sha = self._resolve_version(from_ref)
            from_commit = self[from_sha]
            diff = from_commit.tree.diff(to_commit.tree)
            return diff.patch
        parents = to_commit.parents
        if parents:
            from_commit = parents[0]
            diff = from_commit.tree.diff(to_commit.tree)
            return diff.patch
        opt = GIT_DIFF_REVERSE
        diff = to_commit.tree.diff(flags=opt, empty_tree=True)
        return diff.patch

    def cat_file(self, sha, type='blob'):
        blob = self[sha]
        return blob.data

    def ls_tree(self, ref, recursive=None, size=None, name_only=None):
        obj = self.revparse_single(ref)
        if obj.type == GIT_OBJ_TREE:
            tree_obj = obj
        else:
            tree_obj = obj.tree
        walker = self._walk_tree(tree_obj)
        tree_list = []
        for index, (entry, path) in enumerate(walker):
            mode = '%06o' % entry.filemode
            if mode == '160000':
                objtype = 'commit'  # For git submodules
            elif mode == '040000':
                objtype = 'tree'
            else:
                objtype = 'blob'
            path = "%s/%s" % (path, entry.name) if path else entry.name

            if recursive:
                if objtype == 'tree':
                    _tree = self[entry.id]
                    _tree_list = self._walk_tree(_tree, path)
                    for _index, _entry in enumerate(_tree_list):
                        walker.insert(index + _index + 1, _entry)
                    continue

            if name_only:
                tree_list.append(path)
                continue

            item = [mode, objtype, entry.hex, path]

            if size:
                if objtype == 'blob':
                    blob = self[entry.oid]
                    item = [mode, objtype, entry.hex, blob.size, path]
                else:
                    item = [mode, objtype, entry.hex, '-', path]

            tree_list.append(item)
        return tree_list

    def _walk_tree(self, tree, path=None):
        _list = []
        for entry in tree:
            _list.append((entry, path))
        return _list

    # version: tag, ref, sha
    def _resolve_version(self, version):
        if len(version) == 40:
            return version
        try:
            obj = self.revparse_single(version)
            if obj.type == GIT_OBJ_TAG:
                commit = self[obj.target]
            elif obj.type == GIT_OBJ_COMMIT:
                commit = obj
            elif obj.type == GIT_OBJ_BLOB:
                return None
            elif obj.type == GIT_OBJ_TREE:
                return None
        except KeyError:
            return None
        return commit.hex

    @classmethod
    def is_git_dir(cls, d):
        """ This is taken from the git setup.c:is_git_directory
        function."""
        isdir = os.path.isdir
        join = os.path.join
        if isdir(d) and isdir(join(d, 'objects')) and isdir(join(d, 'refs')):
            headref = join(d, 'HEAD')
            return os.path.isfile(headref) or (
                os.path.islink(headref) and os.readlink(headref).startswith('refs'))
        return False

    # FIXME: UT Segmentation Fault
    def list_config(self):
        config = self.config
        lst = {}
        config.foreach(foreach_pygit2_config, lst)
        return lst

    # FIXME: UT Segmentation Fault
    def get_config(self, key):
        config = self.config
        if key in config:
            return config[key]

    # FIXME
    def list_branch(self):
        return

    # FIXME
    def list_tag(self):
        return

    # FIXME
    def get_commit(self):
        return

    def get_ref(self, ref):
        r = {}
        ref_obj = self.lookup_reference(ref)
        target = self[ref_obj.target]
        r['sha'] = target.hex
        r['type'] = format_pygit2_object_type(target.type)
        r['tree'] = target.tree.hex
        r['shortname'] = format_short_reference_name(ref)
        r['name'] = ref
        return r

    # legency
    def cat_commit(self, sha, commit):
        d = {}
        d['parent'] = [p.hex for p in commit.parents] if commit.parents else []
        d['tree'] = commit.tree.hex
        d['committer'] = format_pygit2_signature(commit.committer)
        d['author'] = format_pygit2_signature(commit.author)
        d['message'], _, d['body'] = commit.message.strip().partition('\n\n')
        d['sha'] = commit.hex
        return d

    # legency
    def cat_tag(self, sha, tag):
        d = {}
        d['name'] = tag.name
        d['tag'] = tag.name
        d['object'] = tag.target.hex
        d['type'] = format_pygit2_object_type(self[tag.target].type)
        d['tagger'] = format_pygit2_signature(tag.tagger)
        d['message'], _, d['body'] = tag.message.strip().partition('\n\n')
        d['sha'] = tag.hex
        return d

    # legency
    def cat_blob(self, sha, blob):
        return blob.data

    # legency
    def cat_tree(self, sha, tree):
        res = []
        for entry in tree:
            mode = '%06o' % entry.filemode
            # FIXME: use pygit2 object
            if mode == '160000':
                objtype = 'commit'  # For git submodules
            elif mode == '040000':
                objtype = 'tree'
            else:
                objtype = 'blob'
            r = {
                'sha': entry.hex,
                'mode': mode,
                'type': objtype,
                'path': entry.name
            }
            res.append(r)
        return res
