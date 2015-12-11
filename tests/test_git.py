# -*- coding: utf-8 -*-

import os
import shutil

from nose.tools import eq_

from vilya.models.project import CodeDoubanProject
from vilya.models import git

from tests.base import TestCase

from vilya.libs import gyt
from vilya.libs.permdir import get_repo_root


class TestGit(TestCase):
    def _path(self, name):
        return os.path.join(get_repo_root(), '%s.git' % name)

    def _path_work_tree(self, name):
        path = os.path.join(get_repo_root(), '%s.work_tree' % name)
        shutil.rmtree(path, ignore_errors=True)
        return path

    def _repo(self, name, bare=True):
        git_path = self._path(name)
        if bare:
            work_tree_path = None
        else:
            work_tree_path = self._path_work_tree(name)
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
        f = open(os.path.join(repo.work_tree, filename), 'w')
        f.write(content)
        f.close()
        rep2 = gyt.repo(repo.path, repo.work_tree, bare=False)
        rep2.call(['add', filename])
        rep2.call(['commit', filename, '-m', message], _env=self.env_for_git)
        return gyt.repo(repo.path).sha()

    def test_create(self):
        git_path = os.path.join(get_repo_root(), 'test_create.git')
        assert not os.path.exists(
            git_path), "git_path should not exist prior repo creation"
        CodeDoubanProject.create_git_repo(git_path)
        assert os.path.exists(
            git_path), "create_git_repo should create git_path"
        refs_file = os.path.join(git_path, 'refs')
        assert os.path.exists(refs_file), \
            "create_git_repo should create a git repo with refs subdir"

    def test_gitrepo_path(self):
        git_path = self._path('test_gitrepo_path')
        CodeDoubanProject.create_git_repo(git_path)
        repo = git.GitRepo(git_path)
        assert repo.path == git_path, "repo.path should be equal to git_path"

    def test_execute_help(self):
        repo = self._repo('test_execute_help')
        res = repo.call(['help'])
        assert res, "executing help should return something"
        eq_(type(res), type(u'a string'))

    def test_repo_is_bare(self):
        repo = self._repo('test_execute_help')
        res = repo.call(['config', 'core.bare'])
        assert res.strip() == 'true', "new git repo should be bare"

    def test_object_type(self):
        repo = self._repo('test_commit', bare=False)
        c1_sha = self._commit(
            repo, 'testfile', 'testcontent', 'testmsg\n\nmsg1body\nmsg1body2')
        assert repo.object_type(c1_sha) == 'commit'
        unused_sha = 'af3d3e81db1559687d1574d368ef578a50ab8971'
        if c1_sha != unused_sha:
            assert repo.object_type(unused_sha) is False

    def test_commit(self):
        repo = self._repo('test_commit', bare=False)
        c1_sha = self._commit(
            repo, 'testfile', 'testcontent', 'testmsg\n\nmsg1body\nmsg1body2')
        assert len(repo.get_branches()) == 1, "should have one ref"
        c1 = repo.get_commit(c1_sha)
        assert c1.message == 'testmsg\n\nmsg1body\nmsg1body2'
        assert c1.message_body == '\nmsg1body\nmsg1body2'
        assert c1.shortlog == 'testmsg'

    def test_get_commit_on_unexisting_commit(self):
        repo = self._repo('test_commit', bare=False)
        c1_sha = self._commit(
            repo, 'testfile', 'testcontent', 'testmsg\n\nmsg1body\nmsg1body2')
        assert repo.get_commit(c1_sha)
        another_sha = '11fb26bace9a2538d200bdc41a1f990bcc06411b'
        if another_sha != c1_sha:
            assert repo.get_commit(another_sha) is None

    def test_two_commit(self):
        repo = self._repo('test_commit', bare=False)
        c1_sha = self._commit(repo, 'testfile', 'content1', 'msg1')
        c2_sha = self._commit(repo, 'testfile', 'content2', 'msg2')
        c2 = repo.get_commit(c2_sha)
        c1 = repo.get_commit(c2.parent)
        assert c1.sha == c1_sha
        assert c1.message == 'msg1'
        assert c2.sha == c2_sha
        assert c2.message == 'msg2'

    def test_merge_commit(self):
        repo = self._repo('test_merge_diff', bare=False)
        self._commit(repo, 'testfile', 'msg')
        not_bare = gyt.repo(repo.path, repo.work_tree)
        self._commit(repo, 'tf1', 'content1', 'msg1')
        not_bare.call('checkout -b test_br')
        sha2 = self._commit(repo, 'tf2', 'content2', 'msg2')
        not_bare.call('checkout master')
        self._commit(repo, 'tf3', 'content3', 'msg3')
        not_bare.call('merge test_br', _env=self.env_for_git)
        sha_merge = repo.pygit2_repo.revparse_single('HEAD').hex
        c = repo.get_commit(sha_merge)
        assert c.parent == sha2, \
            "This is bad, only one parent for a merge commit"

    def test_branches(self):
        repo = self._repo('test_branches', bare=False)
        rep2 = gyt.repo(repo.path, repo.work_tree, bare=False)
        assert repo.get_branches() == []
        self._commit(repo, 'testfile')
        assert repo.get_branches() == ['master']
        rep2.call(['branch', 'test_branch'])
        assert repo.get_branches() == ['master', 'test_branch']
        rep2.call(['checkout', 'test_branch'])
        assert repo.get_branches() == ['test_branch', 'master']
        rep2.call(['branch', 'test_branch牛逼'])
        assert repo.get_branches(
        ) == ['test_branch', 'master', u'test_branch\u725b\u903c']

    def test_rename_detection(self):
        repo = self._repo('test', bare=False)
        self._commit(repo, 'testfile', 'content', 'msg1')
        grepo = gyt.repo(repo.path, work_tree=repo.work_tree)
        grepo.call('mv testfile testfile_new')
        grepo.call('commit -mmv', _env=self.env_for_git)
        assert repo.rename_detection('HEAD') == {'testfile_new': 'testfile'}

    def test_rename_detection_on_first_commit(self):
        repo = self._repo('test', bare=False)
        self._commit(repo, 'testfile', 'content', 'msg1')
        assert repo.rename_detection('HEAD') == {}

    def test_rename_detection_with_manual_mv(self):
        repo = self._repo('test', bare=False)
        content1 = 'a\na\na\na\na\na\na\na\na\na\nAAA'
        self._commit(repo, 'testfile', content1, 'msg1')
        with open(os.path.join(repo.work_tree, 'testfile_new'), 'w') as f:
            f.write(content1)
        grepo = gyt.repo(repo.path, work_tree=repo.work_tree)
        grepo.call('rm testfile')
        grepo.call('add testfile_new')
        grepo.call('commit -ammv', _env=self.env_for_git)
        assert repo.rename_detection('HEAD') == {'testfile_new': 'testfile'}

    # def test_rename_detection_with_manual_mv_and_little_change(self):
    #    repo = self._repo('test', bare=False)
    #    content1 = 'a\na\na\na\na\na\na\na\na\na\nAAA'
    #    content2 = 'a\na\na\na\na\na\na\na\na\na\nBBB'
    #    self._commit(repo, 'testfile', content1, 'msg1')
    #    with open(os.path.join(repo.work_tree, 'testfile_new'), 'w') as f:
    #        f.write(content2)
    #    grepo = gyt.repo(repo.path, work_tree=repo.work_tree)
    #    grepo.call('rm testfile')
    #    grepo.call('add testfile_new')
    #    grepo.call('commit -ammv', _env=self.env_for_git)
    #    assert repo.rename_detection(
    #        'HEAD') == {}, "If files have change, not real rename"
