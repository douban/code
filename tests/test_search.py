# -*- coding: utf-8 -*-

from __future__ import absolute_import
import shutil
import vilya.models.elastic as _el

from nose import SkipTest

from tests.base import TestCase
from tests.utils import delete_project

from vilya.libs.search import code_unittest_client

import vilya.models.elastic.indexer as _index
import vilya.models.elastic.searcher as _search
import vilya.models.elastic.issue_pr_search as _isprsearch
import vilya.models.elastic.src_search as _srcsearch
import vilya.models.elastic.user_search as _usersearch
import vilya.models.elastic.repo_search as _reposearch
from vilya.models.elastic.issue_pr_search import (
    IssuePRSearch, IssueSearch, PullRequestSearch)
from vilya.models.elastic.searcher import SearchEngine
from vilya.models.project_issue import ProjectIssue
from vilya.models.ticket import Ticket
from vilya.models.project import CodeDoubanProject
from vilya.models.sphinx_docs import SphinxDocs
from vilya.models.gist import Gist
from vilya.models.git import make_git_env
from vilya.models.user import User
from vilya.models.pull import PullRequest, add_pull

from vilya.libs.permdir import get_tmpdir

base_yaml_conf = """
sphinx_docs:
    dir: ""
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

src_source1_py = """
from elastic import src_search
def test():
    return 'hello'
"""

src_source2_c = """
#include <stdio.h>
int main()
{
    printf(\"%d\n\", 3);
    return 0;
}
"""


SKIP_TEST = True


def skip_test(*args, **kwargs):
    if SKIP_TEST:
        raise SkipTest(*args, **kwargs)


_index.IndexEngine.c = code_unittest_client
_search.SearchEngine.c = code_unittest_client
_el.CodeSearch.c = code_unittest_client
_el.SearchEngine.c = code_unittest_client
_isprsearch.SearchEngine.c = code_unittest_client
_isprsearch.IndexEngine.c = code_unittest_client
_srcsearch.SearchEngine.c = code_unittest_client
_srcsearch.IndexEngine.c = code_unittest_client
_reposearch.SearchEngine.c = code_unittest_client
_reposearch.IndexEngine.c = code_unittest_client
_usersearch.SearchEngine.c = code_unittest_client
_usersearch.IndexEngine.c = code_unittest_client


class TestProject(TestCase):

    def setUp(self):
        super(TestProject, self).setUp()
        _el.CodeSearch.c.delete()

    def _prj(self):
        delete_project('test')
        prj = CodeDoubanProject.add('test', 'owner', create_trac=False)
        return prj

    def _add(self, prj, fn, content):
        u = self.addUser()
        prj.git.commit_one_file(fn, content, 'add %s' % fn, u)

    def test_empty_project(self):
        p = self._prj()
        _el.CodeSearch.index_a_project_docs(p.id)
        ds = _el.DocsSearch(p.id)
        ret = ds._doc_file_as_dict('path', 'name', 'doc_dir')
        assert not ret

    def test_create_with_index_and_doc(self):
        prj = self._prj()
#        self._add(prj, 'code_config.yaml', base_yaml_conf)
        self._add(prj, 'docs/index.rst', base_index_rst)
        self._add(prj, 'docs/doc1.rst', base_document1_rst)
        sd = SphinxDocs(prj.name)
        sd.build_all()
        _el.CodeSearch.index_a_project_docs(prj.id)
        ds = _el.DocsSearch(prj.id)
        ret = ds._doc_file_as_dict('docs/doc1.rst', 'docs', 'docs')
        assert ret['doc_name'] == 'docs'
        assert ret['url'] == 'docs/rstdocs/doc1/'
        assert ret['content'] == base_document1_rst
        assert ret['type'] == 'docs'
        assert ret['doc_dir'] == 'docs'
        _el.CodeSearch.delete_a_project_docs(prj.id)

    def test_doc_file_datas(self):
        skip_test()
        prj = self._prj()
        self._add(prj, 'docs/index.rst', base_index_rst)
        self._add(prj, 'docs/doc1.rst', base_document1_rst)
        ds = _el.DocsSearch(prj.id)
        big_search_data = ds.doc_file_datas()
        assert len(big_search_data) == 2
        _el.CodeSearch.delete_a_project_docs(prj.id)

    def test_index_a_project_docs(self):
        skip_test()
        prj = self._prj()
        self._add(prj, 'docs/index.rst', base_index_rst)
        self._add(prj, 'docs/doc1.rst', base_document1_rst)
        _el.CodeSearch.index_a_project_docs(prj.id)
        res = _el.CodeSearch.search_a_phrase('Something', from_=0, size=100)
        res = _el.CodeSearch.format_search_result(res)
        assert len(res) == 1
        _el.CodeSearch.delete_a_project_docs(prj.id)

    def test_index_a_project_docs_search_no_result(self):
        skip_test()
        prj = self._prj()
        self._add(prj, 'docs/index.rst', base_index_rst)
        self._add(prj, 'docs/doc1.rst', base_document1_rst)
        _el.CodeSearch.index_a_project_docs(prj.id)
        res = _el.CodeSearch.search_a_phrase(
            'SomethingXXXXXX', from_=0, size=100)
        res = _el.CodeSearch.format_search_result(res)
        assert len(res) == 0
        _el.CodeSearch.delete_a_project_docs(prj.id)

    def test_html_index_a_project_docs(self):
        skip_test()
        prj = self._prj()
        self._add(prj, 'docs/index.html', "<h1>Test html page</h1>")
        _el.CodeSearch.index_a_project_docs(prj.id)
        res = _el.CodeSearch.search_a_phrase('Something', from_=0, size=100)
        res = _el.CodeSearch.format_search_result(res)
        assert len(res) == 0
        _el.CodeSearch.delete_a_project_docs(prj.id)

    def test_cleared_page_not_indexd(self):
        skip_test()
        prj = self._prj()
        self._add(prj, 'docs/index.rst', "aaa")
        _el.CodeSearch.index_a_project_docs(prj.id)
        res = _el.CodeSearch.search_a_phrase('aaa', from_=0, size=100)
        res = _el.CodeSearch.format_search_result(res)
        assert len(res) == 1
        self._add(prj, 'docs/index.rst', "")
        _el.CodeSearch.index_a_project_docs(prj.id)
        res = _el.CodeSearch.search_a_phrase('aaa', from_=0, size=100)
        res = _el.CodeSearch.format_search_result(res)
        assert len(res) == 0
        _el.CodeSearch.delete_a_project_docs(prj.id)

    def test_removed_page_not_indexd(self):
        raise SkipTest("advanced index way doesn't exist now.")
        prj = self._prj()
        self._add(prj, 'docs/index.rst', base_index_rst)
        self._add(prj, 'docs/doc1.rst', 'aaa')
        _el.CodeSearch.index_a_project_docs(prj.id)
        res = _el.CodeSearch.search_a_phrase('aaa', from_=0, size=100)
        res = _el.CodeSearch.format_search_result(res)
        assert len(res) == 1
        prj.git.call('read-tree HEAD')
        temp_dir = get_tmpdir()
        env = make_git_env(is_anonymous=True)
        prj.git.call('--work-tree %s checkout-index --force -a' % temp_dir)
        prj.git.call(['--work-tree', temp_dir, 'rm', 'docs/doc1.rst'])
        prj.git.call(['--work-tree', temp_dir, 'commit', '-m', 'm'], _env=env)
        _el.CodeSearch.index_a_project_docs(prj.id)
        res = _el.CodeSearch.search_a_phrase('aaa', from_=0, size=100)
        res = _el.CodeSearch.format_search_result(res)
        assert len(res) == 0, \
            "Should find no results after removing and reindexing"
        _el.CodeSearch.delete_a_project_docs(prj.id)
        shutil.rmtree(temp_dir)


class TestGist(TestCase):

    def setUp(self):
        super(TestGist, self).setUp()
        _el.CodeSearch.c.delete()

    def _gist(self):
        gist = Gist.add('description', 'testuser', is_public=True)
        return gist

    def test_empty_repo(self):
        skip_test()
        gist = self._gist()
        _el.CodeSearch.index_a_gist(gist.id)
        res = _el.CodeSearch.search_a_phrase('testuser', from_=0, size=100)
        res = _el.CodeSearch.format_search_result(res)
        assert len(res) == 1
        _el.CodeSearch.delete_a_gist(gist.id)

    def test_search_repo_file(self):
        skip_test()
        gist = self._gist()
        gist.update(description='description',
                    gist_names=['file1', 'file2'],
                    gist_contents=['document', 'document'])
        _el.CodeSearch.index_a_gist(gist.id)
        res = _el.CodeSearch.search_a_phrase('file2', from_=0, size=100)
        res = _el.CodeSearch.format_search_result(res)
        assert len(res) == 1
        res = _el.CodeSearch.search_a_phrase('document', from_=0, size=100)
        res = _el.CodeSearch.format_search_result(res)
        assert len(res) == 1
        _el.CodeSearch.delete_a_gist(gist.id)

    def test_change_files(self):
        skip_test()
        gist = self._gist()
        _el.CodeSearch.index_a_gist(gist.id)
        res = _el.CodeSearch.search_a_phrase('description', from_=0, size=100)
        res = _el.CodeSearch.format_search_result(res)
        assert len(res) == 1
        gist.update(description='desc',
                    gist_names=['file1', 'file2'],
                    gist_contents=['document', 'document'])
        _el.CodeSearch.index_a_gist(gist.id)
        res = _el.CodeSearch.search_a_phrase('description', from_=0, size=100)
        res = _el.CodeSearch.format_search_result(res)
        assert len(res) == 0
        res = _el.CodeSearch.search_a_phrase('file2', from_=0, size=100)
        res = _el.CodeSearch.format_search_result(res)
        assert len(res) == 1
        gist.update(description='desc',
                    gist_names=['f1'],
                    gist_contents=['text'])
        _el.CodeSearch.index_a_gist(gist.id)
        res = _el.CodeSearch.search_a_phrase('text', from_=0, size=100)
        res = _el.CodeSearch.format_search_result(res)
        assert len(res) == 1
        res = _el.CodeSearch.search_a_phrase('file2', from_=0, size=100)
        res = _el.CodeSearch.format_search_result(res)
        assert len(res) == 0
        _el.CodeSearch.delete_a_gist(gist.id)


class TestIssue(TestCase):

    def setUp(self):
        super(TestIssue, self).setUp()
        _index.IndexEngine.c.delete()

    def _prj(self, proj_name):
        prj = CodeDoubanProject.add(proj_name, 'owner', create_trac=False)
        return prj

    def test_single_project(self):
        skip_test()
        p = self._prj("test")
        iss1 = ProjectIssue.add(title='title1', description='desc1',
                                creator='owner', project=p.id)
        IssueSearch.index_a_project_issue(p)
        res = IssueSearch.search_a_phrase('owner', p.id)
        res = SearchEngine.decode(res, ('issue_id',))
        res = [id for id, in res]
        assert len(res) == 1
        assert res[0] == iss1.id
        iss2 = ProjectIssue.add(title='title2', description='desc2',
                                creator='owner', project=p.id)
        IssueSearch.index_a_project_issue(p)
        res = IssueSearch.search_a_phrase('owner', p.id)
        res = SearchEngine.decode(res, ('issue_id',))
        res = [id for id, in res]
        assert len(res) == 2
        assert iss1.id in res
        assert iss2.id in res

    def test_multiple_project(self):
        skip_test()
        p1 = self._prj("test_1")
        p2 = self._prj("test_2")
        iss1 = ProjectIssue.add(title='title1', description='desc1',
                                creator='owner', project=p1.id)
        iss2 = ProjectIssue.add(title='title1', description='desc1',
                                creator='owner', project=p2.id)
        IssueSearch.index_a_project_issue(p1)
        IssueSearch.index_a_project_issue(p2)
        res = IssueSearch.search_a_phrase('title1', p1.id)
        res = SearchEngine.decode(res, ('issue_id',))
        res = [id for id, in res]
        assert len(res) == 1
        assert res[0] == iss1.id
        res = IssueSearch.search_a_phrase('title1', p2.id)
        res = SearchEngine.decode(res, ('issue_id',))
        res = [id for id, in res]
        assert len(res) == 1
        assert res[0] == iss2.id


class TestPullRequest(TestCase):

    def setUp(self):
        super(TestPullRequest, self).setUp()
        _index.IndexEngine.c.delete()

    def _prj(self, proj_name, owner_id, fork_from=None):
        prj = CodeDoubanProject.add(proj_name, owner_id, create_trac=False,
                                    fork_from=fork_from)
        return prj

    def _add(self, prj, u, fn, content):
        prj.git.commit_one_file(fn, content, 'add %s' % fn, u)

    def test_single_project(self):
        skip_test()
        u_to = User("admin")
        u_from = User("testuser")
        to_proj = self._prj("test", "admin")
        self._add(to_proj, u_to, "README.md", "hi")
        from_proj = self._prj("testuser/test", "testuser", to_proj.id)
        self._add(from_proj, u_from, "README.md", "hello")
        pullreq = PullRequest.open(from_proj, "master", to_proj, "master")
        ticket = Ticket(None, None, to_proj.id, "title", "desc", "testuser",
                        None, None)
        pullreq = add_pull(ticket, pullreq, u_from)
        ticket = pullreq.ticket
        PullRequestSearch.index_a_project_pr(to_proj)
        res = PullRequestSearch.search_a_phrase('title', to_proj.id)
        res = SearchEngine.decode(res, ('to_proj_id',))
        res = [id for id, in res]
        assert len(res) == 1


class TestProjectIssuePR(TestCase):

    def setUp(self):
        super(TestProjectIssuePR, self).setUp()
        _index.IndexEngine.c.delete()

    def _prj(self, proj_name, owner_id, fork_from=None):
        prj = CodeDoubanProject.add(proj_name, owner_id, create_trac=False,
                                    fork_from=fork_from)
        return prj

    def _add(self, prj, u, fn, content):
        prj.git.commit_one_file(fn, content, 'add %s' % fn, u)

    def test_single_project(self):
        skip_test()
        u_to = User("admin")
        u_from = User("testuser")
        to_proj = self._prj("test", "admin")
        self._add(to_proj, u_to, "README.md", "hi")
        from_proj = self._prj("testuser/test", "testuser", to_proj.id)
        self._add(from_proj, u_from, "README.md", "hello")
        pullreq = PullRequest.open(from_proj, "master", to_proj, "master")
        ticket = Ticket(None, None, to_proj.id, "title", "desc", "testuser",
                        None, None)
        pullreq = add_pull(ticket, pullreq, u_from)

        iss = ProjectIssue.add(title='title1', description='desc1',
                               creator='owner', project=to_proj.id)
        IssuePRSearch.index_a_project(to_proj)
        res = IssueSearch.search_a_phrase('title1', to_proj.id)
        res = SearchEngine.decode(res, ('issue_id',))
        res = [id for id, in res]
        assert len(res) == 1
        assert res[0] == iss.id
        res = PullRequestSearch.search_a_phrase('title', to_proj.id)
        res = SearchEngine.decode(res, ('issue_id',))
        res = [id for id, in res]
        assert len(res) == 1


class TestSrcSearch(TestCase):

    def setUp(self):
        super(TestSrcSearch, self).setUp()
        _srcsearch.IndexEngine.c.delete()
        _srcsearch.IndexEngine.c.put('')
        _srcsearch.SrcSearch.update_mapping()

    def _prj(self):
        delete_project('test')
        prj = CodeDoubanProject.add('test', 'owner', create_trac=False)
        return prj

    def _add(self, prj, fn, content):
        u = self.addUser()
        prj.git.commit_one_file(fn, content, 'add %s' % fn, u)

    def test_get_src_indexes_from_project(self):
        p = self._prj()
        self._add(p, 'index.rst', base_index_rst)
        self._add(p, 'yaml.conf', base_yaml_conf)
        self._add(p, 'src/source1.py', src_source1_py)
        self._add(p, 'src/source2.c', src_source2_c)
        indexes = _srcsearch.SrcSearch.get_src_indexes_from_project(p)
        assert len(indexes) == 4

        indexes_values = [v for k, v in indexes]
        names = [data['name'] for data in indexes_values]
        for name in ['index.rst', 'yaml.conf', 'src/source1.py',
                     'src/source2.c']:
            assert name in names

        index_obj_ids = [(k, v['id']) for k, v in indexes]
        for index_id, obj_id in index_obj_ids:
            assert str(p.id) + obj_id == index_id

        name_data_dict = {data['name']: data for data in indexes_values}
        assert name_data_dict['src/source1.py']['language'] == 'Python'
        assert name_data_dict['src/source2.c']['language'] == 'C'
        assert name_data_dict['yaml.conf']['language'] == 'Text'
        assert name_data_dict['index.rst']['language'] == 'Text'
        for data in indexes_values:
            assert data['project'] == p.name

    def test_single_project_index(self):
        skip_test()
        p = self._prj()
        self._add(p, 'index.rst', base_index_rst)
        self._add(p, 'yaml.conf', base_yaml_conf)
        self._add(p, 'src/source1.py', src_source1_py)
        _srcsearch.SrcSearch.index_a_project(p)
        ids = _srcsearch.SrcSearch.query_a_project_objs(p.name, fields=('id',))
        assert len(ids) == 3

        self._add(p, 'src/source2.c', src_source2_c)
        _srcsearch.SrcSearch.update_a_project_index(p)
        ids = _srcsearch.SrcSearch.query_a_project_objs(p.name, fields=('id',))
        assert len(ids) == 4

        _srcsearch.SrcSearch.delete_a_project_index(p)
        ids = _srcsearch.SrcSearch.query_a_project_objs(p.name, fields=('id',))
        assert len(ids) == 0


class TestRepoSearch(TestCase):

    def setUp(self):
        super(TestRepoSearch, self).setUp()
        _reposearch.IndexEngine.c.delete()

    def test_multiple_project_index(self):
        skip_test()
        for i in range(5):
            CodeDoubanProject.add('test%s' % i, 'owner', create_trac=False)
        _reposearch.RepoSearch.index_repos()
        objs = _reposearch.RepoSearch.query_repo_objs()
        assert len(objs) == 5


class TestUserSearch(TestCase):

    def setUp(self):
        super(TestUserSearch, self).setUp()
        _usersearch.IndexEngine.c.delete()

    def test_multiple_project_index(self):
        skip_test()
        for i in range(5):
            CodeDoubanProject.add(
                'test%s' % i, 'owner%s' % i, create_trac=False)
        _usersearch.UserSearch.index_users()
        objs = _usersearch.UserSearch.query_user_objs()
        assert len(objs) == 5
