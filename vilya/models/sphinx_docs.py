# coding: utf-8
import pickle
import tempfile
import os
import logging
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
debug = logger.debug
warn = logger.warn
import subprocess as sp
import shutil
import datetime as dt
from urllib import quote

import sphinx  # noqa Some pickles need this import

from vilya.libs.store import mc
from vilya.libs.gyt import GytRepoNotInited, GytError
from vilya.libs.permdir import get_tmpdir, get_repo_root
from vilya.models.project import CodeDoubanProject
from vilya.models.consts import (
    DOC_EXT, SPHINX_BUILD_DOCTREES,
    SPHINX_BUILDER_TYPES, SPHINX_DEFAULT_CHECKOUT_ROOT)

DEFAULT_BUILDER = 'pickle'
ENABLED_BUILDERS = SPHINX_BUILDER_TYPES

LAST_BUILD_MC_KEY = 'sphinx-docs:%s:last_build:v2'
LAST_TREE_HASH_MC_KEY = 'sphinx-docs:%s:%s:last_tree_hash:v1'


def _move_to_dir(fromd, tod):
    shutil.rmtree(tod, ignore_errors=True)
    shutil.copytree(fromd, tod)
    shutil.rmtree(fromd)


def _export_docs_tree(project_id, tree_hash, temp_dir):
    _call = CodeDoubanProject.get(project_id).git.call
    debug('Exporting docs tree')
    _call('read-tree --empty')
    try:
        _call('read-tree %s' % tree_hash)
    except GytError as e:
        if 'failed to unpack tree object' in e.args[2]:
            return False, 'failed to unpack tree object'
        else:
            raise
    # TODO use gyt repo to handle worktree
    _call('--work-tree %s checkout-index --force -a' % temp_dir)
    debug('Checked out the docs content work-tree')
    return True, ''


def _tree_hash(project_id, path):
    _call = CodeDoubanProject.get(project_id).git.call
    return _call('rev-parse HEAD:%s' % path, _raise=False)


def _builder_conf(project_id, builder_name):
    prj = CodeDoubanProject.get(project_id)
    if not prj.conf.get('docs'):
        return {'dir': builder_name}
    conf = prj.conf['docs'].get(builder_name, False)
    if not conf:
        return {'dir': builder_name}
    if 'dir' not in conf:
        conf['dir'] = builder_name  # When no explicit dir, use the name
    if 'checkout_root' not in conf:
        conf['checkout_root'] = SPHINX_DEFAULT_CHECKOUT_ROOT
    return conf


def _builders_list(project_id):
    prj = CodeDoubanProject.get(project_id)
    if not prj.conf['docs']:
        return [DEFAULT_BUILDER]
    blds = [(v.get('sort'), k) for k, v in prj.conf['docs'].items()]
    blds = sorted(blds)
    blds = [_[1] for _ in blds]
    return blds


def _check_conf(conf):
    assert isinstance(conf, dict), "Docs config must be a dict"
    vs = conf.values()
    assert all(isinstance(_, dict) for _ in vs), "All docs confs must be dicts"
    assert all(
        _.get('builder', DEFAULT_BUILDER) in ENABLED_BUILDERS for _ in vs), (
        "All docs confs must have a builder chosen in %s (choose %s if unsure)"
        % (ENABLED_BUILDERS, DEFAULT_BUILDER))


def guess_builder_from_path(builders, proj, path):
    assert len(builders) > 0, "Need at least one builder"
    for builder_name in builders:
        if (path == "/%s/docs/%s" % (proj, builder_name) or
                path.startswith("/%s/docs/%s/" % (proj, builder_name))):
            return builder_name, True
    else:
        return builders[0], False  # First default, and implicit


class SphinxDocs(object):  # TODO rename this is not sphinx-only
    builds_logs = []
    disabled_reason = 'Unknown reason'

    def __init__(self, project_name, allow_old_conf=True):
        project = CodeDoubanProject.get_by_name(project_name)
        assert project, "Need existing project"
        self.project_id = project.id
        # if not project or not is_git_dir(project.git_path):
        if not project:
            self.enabled = False
            self.disabled_reason = "No project +_+"
            return
        try:
            self.conf_new = project.conf.get('docs', None)
        except GytRepoNotInited:
            self.enabled = False
            self.disabled_reason = "No project +_+"
            return

        if self.conf_new:
            try:
                _check_conf(self.conf_new)
            except AssertionError, err:
                logging.warning("Docs config error: %s" % err)
                self.enabled = False
                self.disabled_reason = str(err)
                return
        self.enabled = True
        self.builders = _builders_list(project.id)
        mc.set(LAST_BUILD_MC_KEY % self.project_id, None)

    def last_build_info(self):
        return mc.get(LAST_BUILD_MC_KEY % self.project_id)

    def need_rebuild(self):
        last_build = self.last_build_info()
        if not last_build or not last_build['builds']:
            return True
        for builder_name in self.builders:
            builder = self.get_builder(builder_name)
            if builder.need_rebuild():
                return True
        return False

    def _save_build_state(self, status, message=''):
        last_build = {
            'message': message,
            'date': dt.datetime.now(),
            'status': status,
            'builds': self.builds_logs,
        }
        mc.set(LAST_BUILD_MC_KEY % self.project_id, last_build)

    def build_all(self):
        self.builds_logs = []
        self._save_build_state('started')
        if not self.enabled:
            self._save_build_state('disabled', self.disabled_reason)
            return 'disabled'
        builder_name = ''
        for builder_name in self.builders:
            self._build_one(builder_name)

    def _build_one(self, builder_name):
        debug("Starting full build for %s" % builder_name)
        self._save_build_state('exported')
        builder = None
        try:
            success = True
            builder = self.get_builder(builder_name)
            ok, status = builder.prepare()
            if not ok:
                self._save_build_state(status)
                return
            ok, build_status = builder.build()
            self.builds_logs.append(build_status)
            self._save_build_state('building')
            if not ok:
                success = False
                self._save_build_state('FAILED')
                warn("Warning! Unable to build %s" % builder_name)
            else:
                self._save_build_state('building')
            if success:
                builder.move_to_permdir()
                self._save_build_state('success')
            else:
                self._save_build_state('FAILED')
        finally:
            if builder:
                builder.clean_up()

    def get_builder(self, builder_name=None):
        if not builder_name:
            builder_name = self.builders[0]  # First is default
        assert builder_name in self.builders
        if builder_name not in self.conf_new:
            builder_type = DEFAULT_BUILDER
        elif 'builder' not in self.conf_new[builder_name]:
            builder_type = DEFAULT_BUILDER
        else:
            builder_type = self.conf_new[builder_name]['builder']
        assert builder_type in ENABLED_BUILDERS, \
            "builder type %s unknown" % builder_type
        builders_map = {
            'pickle': SphinxDocBuilderPickle,
            'raw': DocBuilderRaw,
            'html': SphinxDocBuilderDefault,
        }
        assert set(builders_map.keys()) == set(ENABLED_BUILDERS)
        bc = builders_map[builder_type]
        retval = bc(builder_name, self.project_id)
        return retval

    def get_url_from_path(self, path):
        for builder_name in self.builders:
            builder = self.get_builder(builder_name)
            if path.startswith("%s/" % builder.dir):
                path = path.replace(builder.dir, "", 1)
                bd = builder
                return quote(bd.get_url_from_path(path))


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


class AbstractDocBuilder(object):
    needed_form_vars = []
    template = False
    slash_urls = False
    static_prefixes = []
    redirects = {}
    masterdoc = 'index'

    def __init__(self, builder, project_id):
        self.builder = builder
        self.project_id = project_id
        prj = CodeDoubanProject.get(project_id)
        self.docs_dir = os.path.join(get_repo_root(),
                                     prj.name + DOC_EXT, builder)
        self.config = _builder_conf(project_id, builder)
        self.dir = self.config['dir']
        self.temp_dir = None
        self.temp_dir_root = None

    def file_is_static(self, path):
        return any(path.startswith(_) for _ in self.static_prefixes)

    def build(self):
        raise NotImplementedError()

    def template_data(self, path, form_vars):
        raise NotImplementedError()

    def raw_content(self, path, form_vars):
        raise NotImplementedError()

    def file_content(self, path):
        fp = os.path.join(self._path(), path)
        if not os.path.exists(fp):
            debug("Path do not exist: %s" % fp)
            return False
        with open(fp) as f:
            content = f.read()
        return content

    def _path(self, tmp=False):
        if tmp:
            assert self.temp_dir
            path = os.path.join(self.temp_dir, '.build', self.builder)
        else:
            path = os.path.join(self.docs_dir, '.build', self.builder)
        return path

    def prepare(self):
        self.temp_dir_root = tempfile.mkdtemp(
            prefix='sphinx_docs_', dir=get_tmpdir())
        if self.config['checkout_root']:
            tree_hash = _tree_hash(self.project_id, '')
        else:
            tree_hash = _tree_hash(self.project_id, self.dir)
        if not tree_hash or not self.has_content():
            warn("No docs directory in project repo at HEAD for builder %s" %
                 self.builder)
            return False, 'no_doc_dir_found'
        mc.set(LAST_TREE_HASH_MC_KEY % (self.project_id,
                                        self.builder), tree_hash)

        if os.path.exists(self.docs_dir):
            shutil.rmtree(self.docs_dir, ignore_errors=True)
        try:
            os.makedirs(self.docs_dir)
        except OSError:
            pass
        ret, msg = _export_docs_tree(
            self.project_id, tree_hash, self.temp_dir_root)
        if not ret:
            return False, msg
        if self.config['checkout_root']:
            self.temp_dir = os.path.join(self.temp_dir_root, self.dir)
        else:
            self.temp_dir = self.temp_dir_root
        return True, 'success'

    def has_content(self):
        tree_hash = _tree_hash(self.project_id, self.dir)
        return bool(tree_hash)

    def move_to_permdir(self):
        debug('Moving to permdir: %s -> %s' % (self.temp_dir, self.docs_dir))
        _move_to_dir(self.temp_dir, self.docs_dir)

    def clean_up(self):
        if self.temp_dir_root and os.path.isdir(self.temp_dir_root):
            shutil.rmtree(self.temp_dir_root)
        mc.set(LAST_TREE_HASH_MC_KEY, None)
        mc.set(LAST_BUILD_MC_KEY, None)

    def need_rebuild(self):
        last_tree_hash = mc.get(
            LAST_TREE_HASH_MC_KEY % (self.project_id, self.builder))
        if self.config['checkout_root']:
            current_tree_hash = _tree_hash(self.project_id, '')
        else:
            current_tree_hash = _tree_hash(self.project_id, self.dir)
        if not last_tree_hash:
            return True
        if last_tree_hash != current_tree_hash:
            return True
        return False

    def with_comment(self):
        return self.config.get('with_comment', True)


class SphinxDocBuilder(AbstractDocBuilder):
    static_prefixes = ['_images', '_sources', '_static', '_downloads']

    def build(self):
        debug('Starting SphinxDocBuilder build')
        cmd = self._make_cmd()
        # TODO lock this dir!
        debug('Building sphinx: %s' % ' '.join(cmd))
        process = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE)
        debug('Process Popened')
        out, err = process.communicate()
        debug('Process communicated')
        returncode = process.returncode
        status = {
            'builder': self.builder,
            'out': out,
            'error': err,
            'returncode': returncode,
            'command': cmd,
        }
        if returncode != 0:
            debug("Error building SphinxDocBuilder %s" % err)
        return returncode == 0, status

    def _make_cmd(self):
        assert self.temp_dir
        sphinx_builder = self.config.get('builder', self.builder)  # noqa TODO rm self.builder when no more old config
        assert sphinx_builder in [
            'pickle', 'html'], "sphinx builder %s unknown" % sphinx_builder
        options = []
        prj = CodeDoubanProject.get(self.project_id)
        default_options = {
            'master_doc': self.masterdoc,
            'source_suffix': '.rst',
            'html_short_title': prj.name,
        }
        options_dict = default_options.copy()
        if self.config:
            options_dict.update(self.config)
        for k, v in options_dict.items():
            options.extend(['-D', '%s=%s' % (k, v)])
        cmd = [
            'sphinx-build',
            '-a',  # -- write all files; default is to only write new and changed files
            '-E',  # -- don't use a saved environment, always read all files
            '-b', sphinx_builder,  # -- builder to use
            '-D', 'project=%s' % prj.name,
            # -- override a setting in configuration
        ]
        cmd += options
        # -- path for the cached environment and doctree files
        cmd += ['-d', os.path.join(self.temp_dir, SPHINX_BUILD_DOCTREES)]
        cmd += ['-q']
        if self._has_sphinx_conf():
            # -- path where configuration file (conf.py) is located
            cmd += ['-c', self.temp_dir]
        else:
            cmd += ['-C']  # No conf.py file
        cmd += [self.temp_dir, self._path(tmp=True)]
        return cmd

    def _has_sphinx_conf(self):
        sphinx_conf = os.path.join(self.temp_dir, 'conf.py')
        return os.path.exists(sphinx_conf)


class SphinxDocBuilderPickle(SphinxDocBuilder):
    template = 'sphinx_docs.html'
    needed_form_vars = ['q']
    slash_urls = True
    redirects = {'index': ''}

    def get_url_from_path(self, path):
        t = path.partition('/')[2]
        t = t.rpartition('.')[0]
        return 'docs/%s/%s/' % (self.builder, t)

    def template_data(self, path, form_vars):
        tdt = _unpickled(self._path(), path)
        if path == 'search':
            q = form_vars['q']
            tdt['searchresult'] = _search(self._path(), q)
        return tdt


class SphinxDocBuilderDefault(SphinxDocBuilder):
    redirects = {'': 'index.html'}

    def raw_content(self, path, form_vars):
        fp = os.path.join(self._path(), path)
        if not os.path.exists(fp):
            debug("Path do not exist: %s" % fp)
            return False
        with open(fp) as f:
            content = f.read()
        return content

    def get_url_from_path(self, path):
        t = path.partition('/')[2]
        t = t.rpartition('.')[0]
        return "docs/%s/%s.html" % (self.builder, t)


class DocBuilderRaw(AbstractDocBuilder):
    redirects = {'': 'index.html'}

    def build(self):
        debug('Starting DocBuilderRaw build')
        target_dir = self._path(tmp=True)
        ignore = shutil.ignore_patterns(('.build',))
        debug("Copying tree from %s to %s" % (self.temp_dir, target_dir))
        shutil.copytree(self.temp_dir, target_dir, ignore=ignore)
        status = {
            'builder': self.builder,
            'out': 'tree copied to .build/raw',
            'error': '',
            'returncode': None,
            'command': ['shutil.copytree(%s, %s)' % (
                self.temp_dir, target_dir)],
        }
        return True, status

    def file_is_static(self, path):
        return True

    def raw_content(self, path, form_vars):
        fp = os.path.join(self._path(), path)
        if not os.path.exists(fp):
            debug("Path do not exist: %s" % fp)
            return False
        with open(fp) as f:
            content = f.read()
        os.remove(fp)
        return content

    def get_url_from_path(self, path):
        t = path.partition('/')[2]
        return "docs/%s/%s" % (self.builder, t)


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
