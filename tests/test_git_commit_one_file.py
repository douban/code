# -*- coding: utf-8 -*-

import os

from vilya.models.project import CodeDoubanProject
from vilya.models import git

from tests.base import TestCase
from tests.utils import mkdtemp

from vilya.libs import gyt
from vilya.libs.permdir import get_repo_root


class TestGit(TestCase):

    @property
    def u(self):
        return self.addUser()

    def _path(self, name):
        return os.path.join(get_repo_root(), '%s.git' % name)

    def _path_work_tree(self, name):
        return os.path.join(get_repo_root(), '%s.work_tree' % name)

    def _repo(self, name, bare=True):
        git_path = self._path(name)
        if bare:
            work_tree_path = None
        else:
            work_tree_path = self._path_work_tree(name)
            if not os.path.exists(work_tree_path):
                os.mkdir(work_tree_path)
        try:
            CodeDoubanProject.create_git_repo(git_path)
        except:
            pass
        repo = git.GitRepo(git_path, work_tree=work_tree_path)
        return repo

    def _commit(self, repo, filename, content='testcontent',
                message='testmessage'):
        # TODO allow commiting more than one file
        assert os.path.exists(repo.work_tree), \
            "repo.work_tree must exist, check if repo has been created with bare=False"  # noqa
        path = os.path.join(repo.work_tree, filename)
        dir_ = os.path.dirname(path)
        if not os.path.exists(dir_):
            os.makedirs(os.path.dirname(path))
        f = open(path, 'w')
        f.write(content)
        f.close()
        rep2 = gyt.repo(repo.path, repo.work_tree, bare=False)
        rep2.call(['add', filename])
        rep2.call(['commit', filename, '-m', message], _env=self.env_for_git)
        return gyt.repo(repo.path).sha()

    def test_simple_commit(self):
        repo = self._repo('test', bare=False)
        self._commit(repo, 'testfile1', 'content1', 'msg1')
        src = repo.get_src('testfile1')
        assert src == ('blob', u'content1')
        repo.commit_one_file('testfile1', 'content1 modified',
                             'change1', self.u, orig_hash=hash('content1'))
        src = repo.get_src('testfile1')
        assert src == ('blob', u'content1 modified')

    def test_simple_commit_do_not_delete_other_files(self):
        repo = self._repo('test', bare=False)
        self._commit(repo, 'testfile1', 'content1', 'msg1')
        self._commit(repo, 'testfile2', 'content2', 'msg2')
        repo.commit_one_file('testfile1', 'content1 modified',
                             'change1', self.u, orig_hash=hash('content1'))
        src = repo.get_src('testfile1')
        assert src == ('blob', u'content1 modified')
        type_, files = repo.get_src('')
        assert any(d['path'] == 'testfile2' for d in files), \
            "testfile2 should exists in root tree"
        src = repo.get_src('testfile2')
        assert src == ('blob', u'content2')

    def test_commit_in_inner_directory(self):
        repo = self._repo('test', bare=False)
        self._commit(repo, 'test/file1', 'content1', 'msg1')
        src = repo.get_src('test/file1')
        assert src == ('blob', u'content1')
        repo.commit_one_file('test/file1', 'content1 modified',
                             'change1', self.u, orig_hash=hash('content1'))
        src = repo.get_src('test/file1')
        assert src == ('blob', u'content1 modified')

    def test_create_file(self):
        repo = self._repo('test', bare=False)
        self._commit(repo, 'file1', 'content1', 'msg1')
        repo.commit_one_file(
            'file2', 'content2 created', 'create1', self.u)
        assert repo.cat('HEAD:file1') == 'content1'
        assert repo.cat('HEAD:file2') == 'content2 created'

    def test_create_first_file(self):
        repo = self._repo('test', bare=False)
        repo.commit_one_file(
            'file1', 'content1 created', 'create1', self.u)
        assert repo.cat('HEAD:file1') == 'content1 created'

    def test_create_first_file_and_more(self):
        repo = self._repo('test', bare=False)
        repo.commit_one_file(
            'file1', 'content1 created', 'create1', self.u)
        repo.commit_one_file(
            'file2', 'content2 created', 'create2', self.u)
        repo.commit_one_file(
            'file3', 'content3 created', 'create3', self.u)
        repo.commit_one_file(
            'file4', 'content4 created', 'create4', self.u)
        assert repo.cat('HEAD:file1') == 'content1 created'
        assert repo.cat('HEAD:file2') == 'content2 created'
        assert repo.cat('HEAD:file3') == 'content3 created'
        assert repo.cat('HEAD:file4') == 'content4 created'

    def test_commit_file_on_dirty_index(self):
        repo = self._repo('test', bare=False)
        repo.commit_one_file(
            'file1', 'content1 created', 'create1', self.u)
        repo.commit_one_file(
            'file2', 'content2 created', 'create2', self.u)
        repo.commit_one_file(
            'file1', 'content1 modified', 'modify1', self.u)
        # Now artificially rewind the index tree state
        repo.call('read-tree HEAD^')
        repo.commit_one_file(
            'file2', 'content2 modified', 'modify2', self.u)
        # the latest commit should not have anything related to file1
        assert 'file1' not in repo.call('log -p -n1')

    def test_create_file_in_dir(self):
        repo = self._repo('test', bare=False)
        self._commit(repo, 'test/file1', 'content1', 'msg1')
        repo.commit_one_file(
            'test/file2', 'content2 created', 'create1', self.u)
        assert repo.cat('HEAD:test/file1') == 'content1'
        assert repo.cat('HEAD:test/file2') == 'content2 created'

    def test_simple_commit_in_branch(self):
        repo = self._repo('test', bare=False)
        self._commit(repo, 'testfile1', 'content1', 'msg1')
        tmp_branch = repo.temp_branch_name()
        repo.commit_one_file('testfile1', 'content1 modified', 'change1',
                             self.u, orig_hash=hash('content1'),
                             branch=tmp_branch)
        with mkdtemp() as tmpdir:
            gyt.call(['git', 'clone', repo.path, tmpdir])
            repo_check = gyt.repo(tmpdir, bare=False)
            src = repo_check.call('show HEAD:testfile1')
            assert src == u'content1'
            repo_check.call('checkout master')
            src = repo_check.call('show HEAD:testfile1')
            assert src == u'content1'
            repo_check.call('checkout %s' % tmp_branch)
            src = repo_check.call('show HEAD:testfile1')
            assert src == u'content1 modified'
            repo_check.call('checkout master')
            src = repo_check.call('show HEAD:testfile1')
            assert src == u'content1'

    def test_simple_commit_in_branch_in_subdir(self):
        repo = self._repo('test', bare=False)
        self._commit(repo, 'test/file1', 'content1', 'msg1')
        tmp_branch = repo.temp_branch_name()
        repo.commit_one_file('test/file1', 'content1 modified', 'change1',
                             self.u, orig_hash=hash('content1'),
                             branch=tmp_branch)
        with mkdtemp() as tmpdir:
            gyt.call(['git', 'clone', repo.path, tmpdir])
            repo_check = gyt.repo(tmpdir, bare=False)
            src = repo_check.call('show HEAD:test/file1')
            assert src == u'content1'
            repo_check.call('checkout master')
            src = repo_check.call('show HEAD:test/file1')
            assert src == u'content1'
            repo_check.call('checkout %s' % tmp_branch)
            src = repo_check.call('show HEAD:test/file1')
            assert src == u'content1 modified'
            repo_check.call('checkout master')
            src = repo_check.call('show HEAD:test/file1')
            assert src == u'content1'

    def test_simple_commit_in_branch_creates_branch(self):
        repo = self._repo('test', bare=False)
        self._commit(repo, 'testfile1', 'content1', 'msg1')
        assert repo.get_branches() == ['master']
        tmp_branch = repo.temp_branch_name()
        repo.commit_one_file('testfile1', 'content1 modified', 'change1',
                             self.u, orig_hash=hash('content1'),
                             branch=tmp_branch)
        assert repo.get_branches() == ['master', tmp_branch]

    def test_simple_commit_in_branch_and_delete_branch(self):
        repo = self._repo('test', bare=False)
        self._commit(repo, 'testfile1', 'content1', 'msg1')
        tmp_branch = repo.temp_branch_name()
        repo.commit_one_file('testfile1', 'content1 modified', 'change1',
                             self.u, orig_hash=hash('content1'),
                             branch=tmp_branch)
        assert tmp_branch in repo.get_branches()
        repo.remove_temp_branch(tmp_branch)
        assert tmp_branch not in repo.get_branches()
        assert repo.get_branches() == ['master']

    def test_simple_commit_in_another_branch(self):
        repo = self._repo('test', bare=False)
        self._commit(repo, 'testfile1', 'content1', 'msg1')
        branch = 'mybranch'
        repo.commit_one_file('testfile1', 'content1 modified', 'change1',
                             self.u, orig_hash=hash('content1'), branch=branch)
        assert branch in repo.get_branches()
        assert set(repo.get_branches()) == set(['master', branch])
