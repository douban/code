from vilya.models.project import CodeDoubanProject
from vilya.models.sphinx_docs import SphinxDocs

import nose
from tests.base import TestCase
from tests.utils import delete_project

base_yaml_conf_old = """
sphinx_docs:
    dir: ""
"""

base_yaml_conf = """
docs:
    docs:
        dir: ""
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
        delete_project('test')
        prj = CodeDoubanProject.add('test', 'owner', create_trac=False)
        return prj

    def _add(self, prj, fn, content):
        u = self.addUser()
        prj.git.commit_one_file(fn, content, 'add %s' % fn, u)


class TestDocs(TestDocsHelpers):

    @nose.tools.raises(Exception)
    def test_create_wrong(self):
        sd = SphinxDocs('unexisting_project')
        assert sd.enabled is False

    def test_create_disabled(self):
        prj = self._prj()
        conf = """
        sphinx_docs: ""
        docs:
            docs:
                builder: pickle
        """
        self._add(prj, 'code_config.yaml', conf)
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
        builder = sd.get_builder('docs')
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
        builder = sd2.get_builder('docs')
        assert builder.template
        doc = builder.template_data('', {})
        assert doc['title'] == 'Unit testing sphinx docs'

    def test_create_with_index_and_doc_and_two_builders(self):
        prj = self._prj()
        base_yaml_conf_two_builders = """
        docs:
            docs:
                builder: html
                dir: ""
                html_theme: default
                html_short_title: testsub
            docs2:
                dir: ""
                builder: pickle
        """
        self._add(prj, 'code_config.yaml', base_yaml_conf_two_builders)
        self._add(prj, 'index.rst', base_index_rst)
        self._add(prj, 'doc1.rst', base_document1_rst)
        sd = SphinxDocs(prj.name)
        sd.build_all()
        assert sd.builders == ['docs', 'docs2']
        pickle_builder = sd.get_builder('docs2')
        assert pickle_builder.template
        doc = pickle_builder.template_data('', {})
        assert doc['title'] == 'Unit testing sphinx docs'
        html_builder = sd.get_builder('docs')
        assert not html_builder.template
        raw = html_builder.raw_content('index.html', {})
        assert "<h1>Unit testing sphinx docs" in raw


class TestDocsPages(TestDocsHelpers):
    conf = 'docs: {"pages": {"builder": "raw"}}'
    builder = 'raw'

    def test_pages_mode(self):
        prj = self._prj()
        self._add(prj, 'code_config.yaml', self.conf)
        self._add(prj, 'pages/index.html', self.html1)
        sd = SphinxDocs(prj.name)
        assert sd.builders == ['pages']
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
    docs:
        builder: html
        html_short_title: testsub
        dir: docs
        html_theme: default
    pages:
        builder: raw
        dir: docs
"""
        self._add(prj, 'code_config.yaml', base_yaml_conf_two_builders)
        self._add(prj, 'docs/index.rst', base_index_rst)
        self._add(prj, 'docs/index.html', self.html1)
        self._add(prj, 'docs/doc1.rst', base_document1_rst)
        sd = SphinxDocs(prj.name)
        sd.build_all()
        assert sd.builders == ['docs', 'pages']
        raw_builder = sd.get_builder('pages')
        doc = raw_builder.raw_content('index.html', {})
        assert doc == self.html1
        html_builder = sd.get_builder('docs')
        assert not html_builder.template
        raw = html_builder.raw_content('index.html', {})
        assert "<h1>Unit testing sphinx docs" in raw

    def test_html_and_raw_builders_in_different_dirs(self):
        prj = self._prj()
        base_yaml_conf_two_builders = """
docs:
    docs:
        builder: html
        html_short_title: testsub
        dir: html_docs
        html_theme: default
    pages:
        builder: raw
        dir: pages
"""
        self._add(prj, 'code_config.yaml', base_yaml_conf_two_builders)
        self._add(prj, 'html_docs/index.rst', base_index_rst)
        self._add(prj, 'html_docs/doc1.rst', base_document1_rst)
        self._add(prj, 'pages/index.html', self.html1)
        sd = SphinxDocs(prj.name)
        sd.build_all()
        assert sd.builders == ['docs', 'pages']
        raw_builder = sd.get_builder('pages')
        doc = raw_builder.raw_content('index.html', {})
        assert doc == self.html1
        html_builder = sd.get_builder('docs')
        assert not html_builder.template
        raw = html_builder.raw_content('index.html', {})
        assert "<h1>Unit testing sphinx docs" in raw


class TestDocsPagesNewConf(TestDocsHelpers):
    def test_two_builders_with_other_config_fmt(self):
        prj = self._prj()
        base_yaml_conf_two_builders = """
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
        sphinx_docs:
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
