# -*- coding: utf-8 -*-

import os
import shutil
import pickle
import sphinx  # Some pickles need this import
import logging
import subprocess

from ellen.repo import Jagare
from ellen.utils.process import git_with_path

from vilya.models.consts import SPHINX_BUILDER_TYPES

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
debug = logger.debug
warn = logger.warn


class Armin(object):

    def __init__(self):
        self.repo = None
        self.conf = None
        self.root_path = None
        self.home_path = None

    def get_content(self, path):
        fp = os.path.join(self.root_path, path)
        if not os.path.exists(fp):
            debug("Path do not exist: %s" % fp)
            return False
        with open(fp) as f:
            content = f.read()
        return content


class ArminBuilder(object):

    def __init__(self, option):
        self.option = option
        self._repo = None

    def repo(self):
        if not self._repo:
            self._repo = Jagare(self.option.repo_path)
        return self._repo

    @property
    def hex(self):
        return self.tree_hex

    @property
    def commit_hex(self):
        return self.repo.resolve_commit('HEAD')

    @property
    def tree_hex(self):
        option = self.option
        repo_path = option.repo_path
        builder_dir = option.builder_dir
        if self.option.autodoc:
            hex = _tree_hash(repo_path, '')
        else:
            hex = _tree_hash(repo_path, builder_dir)
        return hex

    def build(self):
        ret = False
        option = self.option
        try:
            if option.builder not in SPHINX_BUILDER_TYPES:
                return None
            checkout_path(option)
            if option.builder in ['raw']:
                ret, status = raw_build(option)
            elif option.builder in ['pickle', 'html']:
                ret, status = sphinx_build(option)
            if ret:
                _move_to_dir(option.outdir, option.builder_doc_path)
        finally:
            _clean_up(option.temp_path)


class ArminOption(object):
    builder = None
    project = None
    temp_path = None
    doc_path = None
    doctree_path = None
    sourcedir = None
    outdir = None

    def __init__(self):
        self.settings = {}

    def settings_list(self):
        _list = []
        _dict = self.settings
        for key in _dict:
            _list.append('-D')
            _list.append("%s=%s" % (key, _dict[key]))
        return _list

# temp path
# get tree hash
# make doc dir
# export doc tree to temp path


def sphinx_build(option):
    cmd = ['sphinx-build']
    # -- write all files; default is to only write new and changed files
    cmd += ['-a']
    cmd += ['-E']  # -- don't use a saved environment, always read all files
    cmd += ['-b', option.builder]  # -- builder to use
    cmd += option.settings_list()
    # -- path for the cached environment and doctree files
    cmd += ['-d', option.doctree_path]
    cmd += ['-q']
    if _has_sphinx_conf(option.sourcedir):
        # -- path where configuration file (conf.py) is located
        cmd += ['-c', option.sourcedir]
    else:
        cmd += ['-C']  # No conf.py file
    cmd += [option.sourcedir, option.outdir]
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()
    returncode = process.returncode
    status = {
        'builder': option.builder,
        'out': out,
        'error': err,
        'returncode': returncode,
        'command': cmd,
    }
    return returncode == 0, status


def raw_build(option):
    ignore = shutil.ignore_patterns(('.build',))
    shutil.copytree(option.sourcedir, option.outdir, ignore=ignore)
    status = {
        'builder': option.builder,
        'out': 'tree copied to .build/raw',
        'error': '',
        'returncode': None,
        'command': ['shutil.copytree(%s, %s)' % (option.sourcedir, option.outdir)],
    }
    return True, status


def _has_sphinx_conf(temp_path):
    sphinx_conf = os.path.join(temp_path, 'conf.py')
    return os.path.exists(sphinx_conf)


def checkout_path(option):
    repo_path = option.repo_path
    autodoc = option.autodoc
    builder_dir = option.builder_dir
    doc_path = option.doc_path
    temp_path = option.temp_path
    if autodoc:
        tree_hash = _tree_hash(repo_path, '')
    else:
        tree_hash = _tree_hash(repo_path, builder_dir)
    try:
        if doc_path and not os.path.isdir(doc_path):
            os.makedirs(doc_path)
    except OSError:
        pass
    _export_docs_tree(repo_path, tree_hash, temp_path)


def read_tree(git_dir, work_dir=None, tree_hash=None):
    git = git_with_path(git_dir, work_dir)
    if tree_hash:
        return git.read_tree(tree_hash)
    else:
        return git.read_tree(empty=True)


def checkout_index(git_dir, work_dir):
    git = git_with_path(git_dir, work_dir)
    return git.checkout_index(force=True, a=True)


def rev_parse(git_dir, work_dir, rev):
    git = git_with_path(git_dir, work_dir)
    return git.rev_parse(rev)


def get_tree_hash(git_dir, work_dir=None, path=None):
    ret = rev_parse(git_dir, work_dir, 'HEAD:%s' % path if path else 'HEAD')
    if int(ret.get('returncode')) == 0:
        return ret.get('stdout').strip('\n')
    return ''


def _move_to_dir(fromd, tod):
    shutil.rmtree(tod, ignore_errors=True)
    shutil.copytree(fromd, tod)
    shutil.rmtree(fromd)


def _clean_up(path):
    if path and os.path.isdir(path):
        shutil.rmtree(path)


def _export_docs_tree(repo_path, tree_hash, temp_path):
    debug('Exporting docs tree')
    read_tree(repo_path)
    read_tree(repo_path, tree_hash=tree_hash)
    checkout_index(repo_path, temp_path)
    debug('Checked out the docs content work-tree')


def _tree_hash(repo_path, path):
    return get_tree_hash(repo_path, path=path)


def _find_tokens(keys, key):
    key = key.lower().strip()
    return [k for k in keys if k.startswith(key)]


def _unpickled(build_path, path):
    gc = _unpickle_global(build_path, "globalcontext.pickle")
    if not gc:
        return {'error': 'Unable to find global context'}
    if not path:
        path = gc['master_doc']
    pk = _unpickle_target(build_path, path, gc)
    if not pk:
        pk = _unpickle_target(
            build_path, path + '/' + gc['master_doc'], gc)  # Hack
    if not pk:
        return {'error': 'Unable to find pickle', 'gc': gc}
    pk['gc'] = gc
    pk['error'] = False
    return pk


def _unpickle_global(build_path, fn):
    fp = os.path.join(build_path, fn)
    if not os.path.exists(fp):
        return False
    with open(fp) as f:
        p = pickle.load(f)
    return p


def _unpickle_target(build_path, path, gc):
    fp = os.path.join(build_path, path)
    fp += gc['file_suffix']
    if not os.path.exists(fp):
        return False
    with open(fp) as f:
        p = pickle.load(f)
    return p


def _search(build_path, q):
    si = _unpickle_global(build_path, "searchindex.pickle")
    toks = _find_tokens(si['terms'].keys(), q)
    results = []
    for tok in toks:
        links = si['terms'][tok]
        if isinstance(links, int):
            links = [links]
        for link in links:
            results.append((si['filenames'][link], si['titles'][link]))
    return results
