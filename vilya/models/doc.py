# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
import tempfile
import mimetypes

from vilya.libs.permdir import get_tmpdir, get_repo_root
from vilya.libs.store import mc
from vilya.libs.rdstore import rds
from vilya.libs.armin import _unpickled, ArminOption, ArminBuilder, _search
from vilya.models.consts import (
    DOC_EXT, SPHINX_BUILDER_TYPES, SPHINX_STATIC_PATHS,
    SPHINX_DEFAULT_CHECKOUT_ROOT, SPHINX_BUILD_DOCTREES)
from vilya.models.project_conf import CodeConf

PROJECT_BUILD_INFO_MC_KEY = "doc:%s:info"
PROJECT_BUILD_TREE_HASH_MC_KEY = "doc:%s:builder:%s:tree"
PROJECT_BUILD_HASH_MC_KEY = "doc:%s:builder:%s:commit"
PROJECT_BUILD_QUEUE_RDS_KEY = "doc:queue"
DEFAULT_SPHINX_DIR = '.build'


class Doc(object):
    template = None

    def __init__(self, project, id, path):
        self.project = project
        self.doc_id = id
        self.doc_path = os.path.join(get_repo_root(),
                                     "%s%s" % (project.name, DOC_EXT),
                                     self.doc_id,
                                     DEFAULT_SPHINX_DIR,
                                     self.doc_id)
        self._content = self.get_file(path)
        self.path = path

    def get_file(self, path):
        raise NotImplementedError('Subclasses should implement this!')

    @property
    def exists(self):
        raise NotImplementedError('Subclasses should implement this!')

    @property
    def is_template(self):
        raise NotImplementedError('Subclasses should implement this!')

    @property
    def content(self):
        raise NotImplementedError('Subclasses should implement this!')

    @property
    def content_type(self):
        raise NotImplementedError('Subclasses should implement this!')


class PickleDoc(Doc):
    template = 'sphinx_docs.html'

    def get_file(self, path):
        tdt = _unpickled(self.doc_path, path)
        return tdt

    @property
    def exists(self):
        content = self.content
        if content and not content.get('error'):
            return True

    @property
    def is_template(self):
        return not any(self.path.startswith(_) for _ in SPHINX_STATIC_PATHS)

    @property
    def content(self):
        return self._content

    def search(self, query):
        content = self._content
        if self.path == 'search':
            content['searchresult'] = _search(self.doc_path, query)
        return content

    @property
    def content_type(self):
        return None


class HTMLDoc(Doc):

    def get_file(self, path):
        fp = os.path.join(self.doc_path, path)
        if not os.path.exists(fp):
            return False
        with open(fp) as f:
            content = f.read()
        return content

    @property
    def exists(self):
        fp = os.path.join(self.doc_path, self.path)
        return os.path.exists(fp)

    @property
    def is_template(self):
        return None

    @property
    def content(self):
        return self._content

    @property
    def content_type(self):
        ct = mimetypes.guess_type(self.path)
        if ct:
            return ct[0]
        return 'application/octet-stream'


class DocBuilder(object):

    def __init__(self, project, builder_name):
        self.project = project
        self.option = get_project_doc_option(project, builder_name)
        self.builder = ArminBuilder(self.option)
        self.builder_name = builder_name

    @property
    def queue_member(self):
        return "%s:%s" % (self.project.id, self.builder_name)

    @property
    def can_build(self):
        # Has the code_config.yaml
        conf = CodeConf(self.project)
        if conf.exists:
            return True

    @property
    def up_to_date(self):
        # Already builds the source
        last_commit_hash = mc.get(PROJECT_BUILD_HASH_MC_KEY % (
            self.project.id, self.builder_name))
        if not last_commit_hash:
            return False
        repo = self.project.repo
        commit_len = len(repo.get_commits(
            self.builder.commit_hex, last_commit_hash))
        if not commit_len:
            return True
        last_tree_hash = mc.get(PROJECT_BUILD_TREE_HASH_MC_KEY % (
            self.project.id, self.builder_name))
        if not last_tree_hash:
            return False
        if last_tree_hash == self.builder.tree_hex:
            return True
        return False

    @property
    def in_queue(self):
        # Already waits for building
        if rds.sismember(PROJECT_BUILD_QUEUE_RDS_KEY,
                         self.queue_member):
            return True

    def enqueue(self):
        rds.sadd(PROJECT_BUILD_QUEUE_RDS_KEY, self.queue_member)

    def dequeue(self):
        rds.srem(PROJECT_BUILD_QUEUE_RDS_KEY, self.queue_member)

    def build(self):
        project = self.project
        builder_name = self.builder_name
        self.builder.option = get_doc_builder_option(project, builder_name)
        self.option = self.builder.option
        self.builder.build()


def doc_exists(project):
    doc_path = os.path.join(get_repo_root(),
                            "%s%s" % (project.name, DOC_EXT))
    if os.path.exists(doc_path):
        return True


def get_doc_builder(conf, id):
    builder = conf.get('builder')
    if builder in SPHINX_BUILDER_TYPES:
        return builder


def get_project_doc_option(project, builder_name):
    option = ArminOption()
    config = get_builder_conf(project.conf, builder_name)
    option.settings.update(config)
    builder_dir = config.get('dir')
    option.builder_dir = builder_dir
    option.autodoc = True if config.get('checkout_root') else False
    return option


def get_doc_builder_option(project, builder_name):
    option = ArminOption()

    repo_path = project.repo_path
    config = get_builder_conf(project.conf, builder_name)
    builder = config.get('builder')
    builder_dir = config.get('dir')

    temp_path = tempfile.mkdtemp(prefix='sphinx_docs_', dir=get_tmpdir())
    doc_path = os.path.join(get_repo_root(), project.name + DOC_EXT, builder)

    builder_doc_path = os.path.join(doc_path, '.build', builder)
    if config.get('checkout_root'):
        autodoc = True
        builder_temp_path = os.path.join(temp_path, builder_dir)
    else:
        autodoc = False
        builder_temp_path = temp_path
    builder_temp_doc_path = os.path.join(builder_temp_path, '.build', builder)

    option.builder = builder
    option.settings['master_doc'] = 'index'
    option.settings['source_suffix'] = '.rst'
    option.settings['html_short_title'] = project.name
    option.settings.update(config)
    option.settings['project'] = project.name  # noqa -- override a setting in configuration
    option.doctree_path = os.path.join(temp_path, SPHINX_BUILD_DOCTREES)
    option.temp_path = temp_path
    option.sourcedir = builder_temp_path
    option.outdir = builder_temp_doc_path
    option.doc_path = doc_path
    option.builder_doc_path = builder_doc_path
    option.builder_dir = builder_dir
    option.autodoc = autodoc
    option.repo_path = repo_path
    return option


def get_builder_conf(project_conf, builder_name):
    if not project_conf.get('docs'):
        return {'dir': builder_name}
    conf = project_conf['docs'].get(builder_name, False)
    if not conf:
        return {'dir': builder_name}
    if 'dir' not in conf:
        conf['dir'] = builder_name  # When no explicit dir, use the name
    if 'checkout_root' not in conf:
        conf['checkout_root'] = SPHINX_DEFAULT_CHECKOUT_ROOT
    return conf
