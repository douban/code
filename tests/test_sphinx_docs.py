
import os

from vilya.libs.permdir import get_tmpdir
from vilya.models.project import CodeDoubanProject
from vilya.models.sphinx_docs import (
    SphinxDocs, guess_builder_from_path)

import nose
from tests.base import TestCase

base_yaml_conf = """
docs:
    pickle:
        dir: ''
        builder: pickle
"""

base_index_rst = """
Unit testing sphinx docs
========================

.. toctree::
   :glob:

   *
"""

base_document1_rst = """
Test doc1
=========

Something here
"""

base_document2_rst = """
Test doc2
=========

Something here
"""


class TestDocsHelpers(TestCase):
    html1 = '<h1>TITLE1**</h1>'

    def _prj(self):
        prj = CodeDoubanProject.get_by_name('test')
        prj.delete()
        prj = CodeDoubanProject.add('test', 'owner', create_trac=False)
        return prj

    def _add(self, prj, fn, content):
        u = self.addUser()
        prj.git.commit_one_file(fn, content, 'add %s' % fn, u)

    def setUp(self):
        self._nb_dirs_in_tempdir = len(os.listdir(get_tmpdir()))
        TestCase.setUp(self)

    def tearDown(self):
        new_nb_dirs_in_tmpdir = len(os.listdir(get_tmpdir()))
        assert self._nb_dirs_in_tempdir == new_nb_dirs_in_tmpdir, (
            "Builder process should not leave dirs in tmpdir")
        TestCase.tearDown(self)


class TestDocsWithoutConf(TestDocsHelpers):

    def test_create_enabled(self):
        prj = self._prj()
        sd = SphinxDocs(prj.name)
        assert sd.enabled is True

    def test_create_with_index_and_doc(self):
        prj = self._prj()
        self._add(prj, 'docs/index.rst', base_index_rst)
        self._add(prj, 'docs/doc1.rst', base_document1_rst)
        sd = SphinxDocs(prj.name)
        sd.build_all()
        builder = sd.get_builder()
        doc = builder.template_data('', {})
        assert doc['title'] == 'Unit testing sphinx docs'

    def test_build_info(self):
        prj = self._prj()
        self._add(prj, 'docs/index.rst', base_index_rst)
        self._add(prj, 'docs/doc1.rst', base_document1_rst)
        sd = SphinxDocs(prj.name)
        sd.build_all()
        bi = sd.last_build_info()
        assert bi['status'] == 'success'

    def test_need_rebuild(self):
        prj = self._prj()
        self._add(prj, 'docs/index.rst', base_index_rst)
        sd = SphinxDocs(prj.name)
        assert sd.need_rebuild()
        sd.build_all()
        assert not sd.need_rebuild()
        self._add(prj, 'docs/doc1.rst', base_document1_rst)
        sd = SphinxDocs(prj.name)  # Bad, should not have to refresh object
        assert sd.need_rebuild()
        sd.build_all()
        assert not sd.need_rebuild()

    def test_create_with_index_and_doc_and_get_again(self):
        prj = self._prj()
        self._add(prj, 'docs/index.rst', base_index_rst)
        self._add(prj, 'docs/doc1.rst', base_document1_rst)
        sd = SphinxDocs(prj.name)
        sd.build_all()
        sd2 = SphinxDocs(prj.name)
        builder = sd2.get_builder()
        assert builder.template
        doc = builder.template_data('', {})
        assert doc['title'] == 'Unit testing sphinx docs'

    def test_create_with_index_and_doc_and_conf_py(self):
        conf_content = """rst_epilog = 'Ahhhhhhhhhhhhhhhh la fin' """
        prj = self._prj()
        self._add(prj, 'docs/index.rst', base_index_rst)
        self._add(prj, 'docs/doc1.rst', base_document1_rst)
        self._add(prj, 'docs/conf.py', conf_content)
        sd = SphinxDocs(prj.name)
        sd.build_all()
        builder = sd.get_builder()
        doc = builder.template_data('', {})
        assert 'Ahhhhhhhhhhhhhhhh' in doc['body']


class TestDocs(TestDocsHelpers):

    @nose.tools.raises(Exception)
    def test_create_wrong(self):
        sd = SphinxDocs('unexisting_project')
        assert sd.enabled is False

    def test_create_disabled(self):
        prj = self._prj()
        sd = SphinxDocs(prj.name)
        assert sd.enabled is True, "should be enabled by default"

    def test_create_enabled(self):
        prj = self._prj()
        self._add(prj, 'code_config.yaml', base_yaml_conf)
        sd = SphinxDocs(prj.name)
        assert sd.enabled is True

    def test_create_with_index_and_doc(self):
        prj = self._prj()
        self._add(prj, 'code_config.yaml', base_yaml_conf)
        self._add(prj, 'index.rst', base_index_rst)
        self._add(prj, 'doc1.rst', base_document1_rst)
        sd = SphinxDocs(prj.name)
        sd.build_all()
        builder = sd.get_builder()
        doc = builder.template_data('', {})
        assert doc['title'] == 'Unit testing sphinx docs'

    def test_build_info(self):
        prj = self._prj()
        self._add(prj, 'code_config.yaml', base_yaml_conf)
        self._add(prj, 'index.rst', base_index_rst)
        self._add(prj, 'doc1.rst', base_document1_rst)
        sd = SphinxDocs(prj.name)
        sd.build_all()
        bi = sd.last_build_info()
        assert bi['status'] == 'success'

    def test_need_rebuild(self):
        prj = self._prj()
        self._add(prj, 'code_config.yaml', base_yaml_conf)
        self._add(prj, 'index.rst', base_index_rst)
        sd = SphinxDocs(prj.name)
        assert sd.need_rebuild()
        sd.build_all()
        assert not sd.need_rebuild()
        self._add(prj, 'doc1.rst', base_document1_rst)
        sd = SphinxDocs(prj.name)  # Bad, should not have to refresh object
        assert sd.need_rebuild()
        sd.build_all()
        assert not sd.need_rebuild()

    def test_create_with_index_and_doc_and_get_again(self):
        prj = self._prj()
        self._add(prj, 'code_config.yaml', base_yaml_conf)
        self._add(prj, 'index.rst', base_index_rst)
        self._add(prj, 'doc1.rst', base_document1_rst)
        sd = SphinxDocs(prj.name)
        sd.build_all()
        sd2 = SphinxDocs(prj.name)
        builder = sd2.get_builder()
        assert builder.template
        doc = builder.template_data('', {})
        assert doc['title'] == 'Unit testing sphinx docs'

    def test_create_with_index_and_doc_and_conf_py(self):
        conf_content = """rst_epilog = 'Ahhhhhhhhhhhhhhhh la fin' """
        prj = self._prj()
        self._add(prj, 'code_config.yaml', base_yaml_conf)
        self._add(prj, 'index.rst', base_index_rst)
        self._add(prj, 'doc1.rst', base_document1_rst)
        self._add(prj, 'conf.py', conf_content)
        sd = SphinxDocs(prj.name)
        sd.build_all()
        builder = sd.get_builder()
        doc = builder.template_data('', {})
        assert 'Ahhhhhhhhhhhhhhhh' in doc['body']

    def test_create_with_index_and_doc_and_two_builders(self):
        prj = self._prj()
        base_yaml_conf_two_builders = """
        docs:
            html:
                dir: ''
                builder: html
            pickle:
                dir: ''
                builder: pickle
        """
        self._add(prj, 'code_config.yaml', base_yaml_conf_two_builders)
        self._add(prj, 'index.rst', base_index_rst)
        self._add(prj, 'doc1.rst', base_document1_rst)
        sd = SphinxDocs(prj.name)
        sd.build_all()
        assert sd.builders == ['html', 'pickle']
        pickle_builder = sd.get_builder('pickle')
        assert pickle_builder.template
        doc = pickle_builder.template_data('', {})
        assert doc['title'] == 'Unit testing sphinx docs'
        html_builder = sd.get_builder('html')
        assert not html_builder.template
        raw = html_builder.raw_content('index.html', {})
        assert "<h1>Unit testing sphinx docs" in raw


class TestDocsPages(TestDocsHelpers):
    conf = """
    docs:
        raw:
            dir: pages
            builder: raw
    """
    builder = 'raw'

    def test_pages_mode(self):
        prj = self._prj()
        self._add(prj, 'code_config.yaml', self.conf)
        self._add(prj, 'pages/index.html', self.html1)
        sd = SphinxDocs(prj.name)
        assert sd.builders == [self.builder]
        assert sd.last_build_info() is None
        sd.build_all()
        assert sd.last_build_info()['status'] == 'success'
        builder = sd.get_builder(sd.builders[0])
        assert builder.raw_content('index.html', {}) == self.html1

    def test_pages_no_docsdir(self):
        prj = self._prj()
        self._add(prj, 'code_config.yaml', self.conf)
        self._add(prj, 'pagesNOT_THE_SAME/index.html', self.html1)
        sd = SphinxDocs(prj.name)
        sd.build_all()
        assert sd.last_build_info()['status'] == 'no_doc_dir_found'
        builder = sd.get_builder(sd.builders[0])
        assert builder.raw_content('index.html', {}) is False

    def test_html_and_raw_builders(self):
        prj = self._prj()
        base_yaml_conf_two_builders = """
        docs:
            html:
                dir: docs
                builder: html
            raw:
                dir: docs
                builder: raw
        """
        self._add(prj, 'code_config.yaml', base_yaml_conf_two_builders)
        self._add(prj, 'docs/index.rst', base_index_rst)
        self._add(prj, 'docs/index.html', self.html1)
        self._add(prj, 'docs/doc1.rst', base_document1_rst)
        sd = SphinxDocs(prj.name)
        sd.build_all()
        assert sd.builders == ['html', 'raw']
        raw_builder = sd.get_builder('raw')
        doc = raw_builder.raw_content('index.html', {})
        assert doc == self.html1
        html_builder = sd.get_builder('html')
        assert not html_builder.template
        raw = html_builder.raw_content('index.html', {})
        assert "<h1>Unit testing sphinx docs" in raw

    def test_html_and_raw_builders_in_different_dirs(self):
        prj = self._prj()
        base_yaml_conf_two_builders = """
        docs:
            html:
                dir: html_docs
                builder: html
            raw:
                builder: raw
                dir: pages
        """
        self._add(prj, 'code_config.yaml', base_yaml_conf_two_builders)
        self._add(prj, 'html_docs/index.rst', base_index_rst)
        self._add(prj, 'html_docs/doc1.rst', base_document1_rst)
        self._add(prj, 'pages/index.html', self.html1)
        sd = SphinxDocs(prj.name)
        sd.build_all()
        assert sd.builders == ['html', 'raw']
        raw_builder = sd.get_builder('raw')
        doc = raw_builder.raw_content('index.html', {})
        assert doc == self.html1
        html_builder = sd.get_builder('html')
        assert not html_builder.template
        raw = html_builder.raw_content('index.html', {})
        assert "<h1>Unit testing sphinx docs" in raw


class TestDocsPagesNewConf(TestDocsHelpers):
    def test_two_builders_with_other_config_fmt(self):
        prj = self._prj()
        base_yaml_conf_two_builders = """
        #sphinx_docs:
        #    dir: "docs"
        #    builders:
        #        - html:
        #            html_theme: default
        #            html_short_title: testsub
        #            dir: html_docs
        #        - raw:
        #            dir: pages
        docs:
            docs:
                builder: html
                html_theme: default
                html_short_title: testsub
                dir: html_docs
            pages:
                builder: raw
        """
        self._add(prj, 'code_config.yaml', base_yaml_conf_two_builders)
        self._add(prj, 'html_docs/index.rst', base_index_rst)
        self._add(prj, 'html_docs/doc1.rst', base_document1_rst)
        self._add(prj, 'pages/index.html', self.html1)
        sd = SphinxDocs(prj.name)
        sd.build_all()
        assert sd.builders == ['docs', 'pages']  # noqa Sorted alphabetically by default
        raw_builder = sd.get_builder('pages')
        doc = raw_builder.raw_content('index.html', {})
        assert doc == self.html1
        html_builder = sd.get_builder('docs')
        assert not html_builder.template
        raw = html_builder.raw_content('index.html', {})
        assert "<h1>Unit testing sphinx docs" in raw

    def test_sort_key(self):
        prj = self._prj()
        base_yaml_conf_two_builders = """
        docs:
            docs:
                builder: html
                html_theme: default
                html_short_title: testsub
                sort: 2
            pages:
                builder: raw
                sort: 1
        """
        self._add(prj, 'code_config.yaml', base_yaml_conf_two_builders)
        sd = SphinxDocs(prj.name)
        assert sd.builders == ['pages', 'docs']

    def test_guess_builder_from_path_found(self):
        bs = ['build1', 'build2']
        pr = 'testprj'
        path = '/testprj/docs/build1/doc1'
        builder, found = guess_builder_from_path(bs, pr, path)
        assert builder == 'build1'
        assert found is True

    def test_guess_builder_from_path_found_second_one(self):
        bs = ['build1', 'build2']
        pr = 'testprj'
        path = '/testprj/docs/build2/doc1'
        builder, found = guess_builder_from_path(bs, pr, path)
        assert builder == 'build2'
        assert found is True

    def test_guess_builder_from_path_not_found(self):
        bs = ['build1', 'build2']
        pr = 'testprj'
        path = '/testprj/docs/build__NOTFOUND/doc1'
        builder, found = guess_builder_from_path(bs, pr, path)
        assert builder == 'build1'
        assert found is False


class TestDocsPagesFromPath(TestDocsHelpers):

    def test_get_url_from_path_sphinx_doc_builder_default(self):
        prj = self._prj()
        base_yaml_conf_two_builders = """
        docs:
            mypages:
                builder: raw
                dir: mypagesdir
                name: Pages
                sort: 1
            mariodocs:
                builder: html
                dir: htmldocs/1
                name: HTMLDocs
                sort: 2
        """
        self._add(prj, 'code_config.yaml', base_yaml_conf_two_builders)
        sd = SphinxDocs(prj.name)
        path = 'htmldocs/1/index.rst'
        url = sd.get_url_from_path(path)
        assert url == 'docs/mariodocs/index.html'

    def test_get_url_from_path_sphinx_doc_builder_pickle_no_subdir(self):
        prj = self._prj()
        base_yaml_conf_two_builders = """
        docs:
            mydocs:
                dir: mydocsdir/6
            pages:
                builder: raw
        """
        self._add(prj, 'code_config.yaml', base_yaml_conf_two_builders)
        sd = SphinxDocs(prj.name)
        path = 'mydocsdir/6/index.rst'
        url = sd.get_url_from_path(path)
        assert url == 'docs/mydocs/index/'

    def test_get_url_from_path_sphinx_doc_builder_pickle_subdir(self):
        prj = self._prj()
        base_yaml_conf_two_builders = """
        docs:
            mydocs:
                dir: mydocsdir
            pages:
                builder: raw
        """
        self._add(prj, 'code_config.yaml', base_yaml_conf_two_builders)
        sd = SphinxDocs(prj.name)
        path = 'mydocsdir/subdir/doc1.rst'
        url = sd.get_url_from_path(path)
        assert url == 'docs/mydocs/subdir/doc1/'

    def test_get_url_from_path_sphinx_doc_raw_builder_no_subdir(self):
        prj = self._prj()
        base_yaml_conf_two_builders = """
        docs:
            mydocs:
                dir: mydocsdir/3
                builder: raw
        """
        self._add(prj, 'code_config.yaml', base_yaml_conf_two_builders)
        sd = SphinxDocs(prj.name)
        path = 'mydocsdir/3/foo.bar'
        url = sd.get_url_from_path(path)
        assert url == 'docs/mydocs/foo.bar'

    def test_get_url_from_path_no_dir(self):
        prj = self._prj()
        base_yaml_conf_two_builders = """
        docs:
            mydocs:
                dir: mydocsdir
            mypages:
                builder: raw

        """
        self._add(prj, 'code_config.yaml', base_yaml_conf_two_builders)
        sd = SphinxDocs(prj.name)
        path = 'mypages/subdir/doc1.html'
        url = sd.get_url_from_path(path)
        assert url == 'docs/mypages/subdir/doc1.html'

    def test_get_url_from_path_doc_builder_raw(self):
        prj = self._prj()
        base_yaml_conf_two_builders = """
        docs:
            mydocs:
                dir: mydocsdir
            mypages:
                builder: raw
                dir: pages/1

        """
        self._add(prj, 'code_config.yaml', base_yaml_conf_two_builders)
        sd = SphinxDocs(prj.name)
        path = 'pages/1/subdir/doc1.html'
        url = sd.get_url_from_path(path)
        assert url == 'docs/mypages/subdir/doc1.html'

    def test_get_url_from_path_old_conf(self):
        prj = self._prj()
        sd = SphinxDocs(prj.name)
        path = 'docs/index.rst'
        url = sd.get_url_from_path(path)
        assert url == 'docs/rstdocs/index/'

    def test_get_url_from_path_complex_src_dir(self):
        prj = self._prj()
        base_yaml_conf_two_builders = """
        docs:
            mypages:
                builder: raw
                dir: blog/output
                name: Blog
                sort: 1

        """
        self._add(prj, 'code_config.yaml', base_yaml_conf_two_builders)
        sd = SphinxDocs(prj.name)
        path = 'blog/output/doc1.html'
        url = sd.get_url_from_path(path)
        assert url == 'docs/mypages/doc1.html'

    def test_get_url_from_path_percent_sign_path(self):
        prj = self._prj()
        sd = SphinxDocs(prj.name)
        path = 'docs/doubanlib%2Fsqlstore.rst'
        url = sd.get_url_from_path(path)
        assert url == 'docs/rstdocs/doubanlib%252Fsqlstore/'
        path = 'docs/%E6%80%A7%E8%83%BD%E6%B5%8B%E8%AF%95.rst'
        url = sd.get_url_from_path(path)
        assert url == 'docs/rstdocs/%25E6%2580%25A7%25E8%2583%25BD%25E6%25B5%258B%25E8%25AF%2595/'  # noqa


class TestAutodoc(TestDocsHelpers):
    conf_py = """
import sys, os
sys.path.insert(0, os.path.abspath('..'))
extensions = ['sphinx.ext.autodoc']
    """
    index_rst = """
Test
====

.. automodule:: testapi
    :members:
    """
    api_py = """
class C(object):
    '''Test C docstring'''
    """
    code_config_yaml = """
    docs:
        mydocs:
            checkout_root: True
            link: http://code.dapps.douban.com//
            builder: pickle
            dir: docs
    """

    def test_use_autodoc_not_configured(self):
        prj = self._prj()
        self._add(prj, 'docs/conf.py', self.conf_py)
        self._add(prj, 'docs/index.rst', self.index_rst)
        self._add(prj, 'testapi.py', self.api_py)
        sd = SphinxDocs(prj.name)
        sd.build_all()
        builder = sd.get_builder()
        doc = builder.template_data('', {})
        assert "Test C docstring" not in doc['body']

    def test_use_autodoc_configured(self):
        prj = self._prj()
        self._add(prj, 'code_config.yaml', self.code_config_yaml)
        self._add(prj, 'docs/conf.py', self.conf_py)
        self._add(prj, 'docs/index.rst', self.index_rst)
        self._add(prj, 'testapi.py', self.api_py)
        sd = SphinxDocs(prj.name)
        sd.build_all()
        builder = sd.get_builder()
        doc = builder.template_data('', {})
        assert "Test C docstring" in doc['body']
