# -*- coding: utf-8 -*-

import os
import shutil
import tempfile
import datetime as dt
from os.path import join as opj

import nose

from tests.base import TestCase
from vilya.libs import gyt

TEST_REPO = '/tmp/test_gyt/repo/.git'

ENV_FOR_GIT = {
    'GIT_AUTHOR_NAME': 'default_test',
    'GIT_AUTHOR_EMAIL': 'default_test@douban.com',
    'GIT_COMMITTER_NAME': 'default_test',
    'GIT_COMMITTER_EMAIL': 'default_test@douban.com',
}

class TestGyt(TestCase):
    def _repo(self, bare=False):
        if bare:
            rep = gyt.repo(self._gd, bare=True, init=True)
        else:
            rep = gyt.repo(self._gd, self._wt, bare=False, init=True)
        return rep

    def _add_file(self, rep, filename, content='', commit=True,
                  commit_msg=None):
        f = open(opj(rep.work_tree, filename), 'w')
        f.write(content)
        f.close()
        rep.call(['add', filename])
        if commit:
            if not commit_msg:
                commit_msg = 'unit test commit msg for %s' % filename
            rep.call(['commit', '-m', commit_msg], _env=ENV_FOR_GIT)

    def setUp(self):
        self._gd = tempfile.mkdtemp(prefix='gyt_gd_')  # Git dir
        self._wt = tempfile.mkdtemp(prefix='gyt_wt_')  # Work tree
        self._gd2 = tempfile.mkdtemp(prefix='gyt_gd2_')  # Git dir
        self._wt2 = tempfile.mkdtemp(prefix='gyt_wt2_')  # Work tree
        self._gdc = tempfile.mkdtemp(prefix='gyt_gd_仓库_')
        self._gds = tempfile.mkdtemp(prefix='gyt_gd_ space')

    def tearDown(self):
        shutil.rmtree(self._gd)
        shutil.rmtree(self._wt)
        shutil.rmtree(self._gd2)
        shutil.rmtree(self._wt2)
        shutil.rmtree(self._gdc)
        shutil.rmtree(self._gds)

    def test_git_call_version(self):
        out = gyt.call(gyt.GIT_EXECUTABLE, 'version')
        assert 'git' in out

    def test_gyt_call_command_as_list(self):
        out = gyt.call(gyt.GIT_EXECUTABLE, ['help', 'init'])
        assert 'git init' in out

    def test_gyt_call_command_as_string(self):
        out = gyt.call(gyt.GIT_EXECUTABLE, ['help', 'init'])
        assert 'git init' in out

    def test_git_check_version(self):
        _, _, ver = gyt.call(gyt.GIT_EXECUTABLE, 'version').split()

        def _ver_num(ver):
            return [int(n) for n in ver.split('.')]
        assert _ver_num(ver) >= _ver_num(gyt.GIT_MIN_VERSION)

    def test_git_call_init(self):
        gyt.repo(self._gd, init=True)
        assert os.path.exists(self._gd)
        assert os.path.exists(opj(self._gd, 'refs'))

    def test_git_call_error(self):
        out = gyt.call(
            gyt.GIT_EXECUTABLE, 'unexisting___command__', _raise=False)
        assert out is False

    def test_git_repo_with_space(self):
        gd_with_space = self._gd + ' with space and 中文'
        wt_with_space = self._wt + ' with space and 中文'
        os.mkdir(gd_with_space)
        os.mkdir(wt_with_space)
        rep = gyt.repo(gd_with_space, wt_with_space, init=True)
        self._add_file(
            rep, 'test_filename', 'content', commit=True, commit_msg='test')
        assert rep
        h = rep.logs()
        assert h
        shutil.rmtree(gd_with_space)
        shutil.rmtree(wt_with_space)

    @nose.tools.raises(gyt.GytError)
    def test_git_call_error_raise(self):
        gyt.call(gyt.GIT_EXECUTABLE, 'unexisting___command__')

    def test_git_call_with_int(self):
        ok = gyt.call(gyt.GIT_EXECUTABLE, 'rev-parse', 123, _raise=False)
        assert ok == False

    def test_git_call_with_int_in_list(self):
        ok = gyt.call([gyt.GIT_EXECUTABLE, 'rev-parse', 123], _raise=False)
        assert ok == False

    def xxxxxx_git_call_with_int_in_list(self):
        # BROKEN, maybe no need to fix? TODO
        ok = gyt.call(gyt.GIT_EXECUTABLE, ['rev-parse', 123], _raise=False)
        assert ok == False

    def test_call_with_unicode(self):
        assert 'aaaaa' == gyt.call(u"echo aaaaa")
        test_str = u"aaaaa太牛了！"
        assert test_str == gyt.call("echo '%s'" % test_str)

    def test_is_git_dir(self):
        assert not gyt.is_git_dir(self._gd)
        gyt.repo(self._gd, init=True)
        assert gyt.is_git_dir(self._gd)

    def test_git_init_with_chinese(self):
        gyt.repo(self._gdc, init=True)
        assert gyt.is_git_dir(self._gdc)

    def test_git_init_with_spaces(self):
        gyt.repo(self._gds, init=True)
        assert gyt.is_git_dir(self._gds)

    def test_fake_git_dir(self):
        os.mkdir(opj(self._gd, 'refs'))
        assert os.path.exists(opj(self._gd, 'refs'))
        assert not gyt.is_git_dir(self._gd)

    def test_init_bare_repo(self):
        rep = gyt.repo(self._gd, init=True)
        assert rep.git_dir == self._gd
        assert rep.is_bare()

    def test_init_repo(self):
        rep = gyt.repo(self._gd, self._wt, init=True)
        assert rep.git_dir == self._gd
        assert not rep.is_bare()

    def test_init_repo_and_get(self):
        rep = gyt.repo(self._gd, init=True)
        assert rep
        rep2 = gyt.repo(self._gd)
        assert rep2
        assert rep.git_dir == rep2.git_dir

    @nose.tools.raises(Exception)
    def test_cannot_double_init(self):
        rep1 = gyt.repo(self._gd, init=True)
        assert rep1
        gyt.repo(self._gd, init=True)

    def test_init_repo_default_behavior(self):
        rep = gyt.repo(self._wt, bare=False, init=True)
        assert not rep.is_bare()
        assert rep.work_tree == self._wt
        assert rep.git_dir == opj(self._wt, gyt.GIT_DIR_DEFAULT)

    def test_bare_clone_repo(self):
        rep = gyt.repo(self._gd, init=True)
        clone = rep.clone(self._gd2, bare=True)
        clone2 = gyt.repo(self._gd2, bare=True)
        assert clone.config('remote.origin.url') == self._gd
        assert clone.is_bare()
        clone2 = gyt.repo(self._gd2)
        assert clone2.config('remote.origin.url') == self._gd
        assert clone2.is_bare()

    def test_not_bare_clone_to_not_bare(self):
        rep = gyt.repo(self._gd, init=True, bare=False)
        clone = rep.clone(self._wt2, bare=False)
        assert not gyt.is_git_dir(self._wt2)
        clone = gyt.repo(self._wt2, bare=False)
        assert clone.config('remote.origin.url') == rep.git_dir
        assert not clone.is_bare()

    def test_bare_clone_to_not_bare(self):
        rep = gyt.repo(self._gd, init=True)
        assert rep.is_bare()
        clone = rep.clone(self._wt2, bare=False)
        assert not gyt.is_git_dir(self._wt2)
        clone = gyt.repo(self._wt2, bare=False)
        assert clone.config('remote.origin.url') == rep.git_dir
        assert not clone.is_bare()

    def test_commit_missing_m(self):
        rep = self._repo()
        # The call below could hang the script
        # if not protected by check_cmd, because
        # git would wait for commit message
        out = rep.call(['commit'], _raise=False)
        assert out is False

    def test_commit_missing_message(self):
        rep = self._repo()
        self._add_file(rep, 'test1', commit=False)
        # Will not work, no message passed
        out = rep.call(['commit', '-m'], _raise=False)
        assert out is False

    def test_head(self):
        rep = self._repo()
        assert rep.head() == 'refs/heads/master'
        assert rep.head(short=True) == 'master'
        self._add_file(rep, 'test1')  # Need one commit before branching
        assert rep.head() == 'refs/heads/master'
        rep.call(['branch', 'test_branch'])
        rep.call(['checkout', 'test_branch'])
        assert rep.head() == 'refs/heads/test_branch'

    def test_refs(self):
        rep = self._repo()
        assert rep.refs() == []
        self._add_file(rep, 'test1')  # Need one commit before branching
        assert len(rep.refs()) == 1
        assert rep.refs() == ['refs/heads/master']
        master_ref = rep.ref_details(rep.refs()[0])
        assert master_ref['type'] == 'commit'
        assert master_ref['name'] == 'refs/heads/master'
        assert master_ref['shortname'] == 'master'
        assert rep.cat(master_ref['sha'], only_type=True) == 'commit'
        rep.call(['branch', 'test_branch'])
        assert rep.refs(short=True) == ['master', 'test_branch']
        assert len(rep.refs()) == 2

    def test_refs_with_chinese(self):
        rep = self._repo()
        self._add_file(rep, 'test1')
        rep.call(['branch', 'test_branch牛逼'])
        assert rep.refs(short=True) == [u'master', u'test_branch\u725b\u903c']

    def test_refs_with_tags(self):
        rep = self._repo()
        self._add_file(rep, 'test1')  # Need one commit before branching
        rep.call(['branch', 'test_branch'])
        assert len(rep.refs()) == 2
        rep.call(['tag', 'test_tag1'], _env=ENV_FOR_GIT)
        assert len(rep.refs()) == 3
        assert len(rep.refs(select='tags')) == 1
        assert len(rep.refs(select='branches')) == 2

    def test_refs_current_first(self):
        rep = self._repo()
        self._add_file(rep, 'test1')  # Need one commit before branching
        rep.call(['branch', 'a_br'])
        rep.call(['branch', 'b_br'])
        assert rep.refs(short=True) == ['a_br', 'b_br', 'master']
        assert rep.head(short=True) == 'master'
        assert rep.refs(
            short=True, current_first=True) == ['master', 'a_br', 'b_br']
        rep.call(['checkout', 'b_br'])
        assert rep.head(short=True) == 'b_br'
        assert rep.refs(short=True) == ['a_br', 'b_br', 'master']
        assert rep.refs(
            short=True, current_first=True) == ['b_br', 'a_br', 'master']

    def test_commit(self):
        rep = self._repo()
        self._add_file(rep, 'test1', commit=False)
        before = dt.datetime.now() - dt.timedelta(seconds=1)
        rep.call(
            "commit -m 'test_msg\n\nmsg_body' --author='test author <ta@example.com>'",  # noqa
            _env=ENV_FOR_GIT)
        after = dt.datetime.now() + dt.timedelta(seconds=1)
        cmt = rep.cat(rep.head())
        assert cmt['author']['name'] == 'test author'
        assert cmt['author']['email'] == 'ta@example.com'
        assert before < cmt['author']['date'] < after
        assert cmt['message'] == 'test_msg'
        assert cmt['body'] == 'msg_body'
        assert cmt['tree'] == rep.call('rev-parse HEAD^{tree}')
        assert cmt['parent'] == []

    def test_commit_using_env(self):
        rep = self._repo()
        self._add_file(rep, 'test1', commit=False)
        before = dt.datetime.now() - dt.timedelta(seconds=1)
        env = {'GIT_AUTHOR_NAME': 'test author',
               'GIT_AUTHOR_EMAIL': 'ta@example.com',
               'GIT_COMMITTER_NAME': 'test commiter',
               'GIT_COMMITTER_EMAIL': 'tc@example.com',
               }
        rep.call("commit -m 'test_msg\n\nmsg_body'", _env=env)
        after = dt.datetime.now() + dt.timedelta(seconds=1)
        cmt = rep.cat(rep.head())
        assert cmt['author']['name'] == 'test author'
        assert cmt['author']['email'] == 'ta@example.com'
        assert before < cmt['author']['date'] < after
        assert cmt['message'] == 'test_msg'
        assert cmt['body'] == 'msg_body'
        assert cmt['tree'] == rep.call('rev-parse HEAD^{tree}')
        assert cmt['parent'] == []

    def test_merge_commit_has_two_parents(self):
        rep = self._repo(bare=False)
        with open(opj(rep.work_tree, 'test1'), 'w') as f:
            f.write('a\nb\nc\n\d')
        rep.call('add test1')
        rep.call('commit -mtest_merge1', _env=ENV_FOR_GIT)
        rep.call('branch br_a')
        rep.call('checkout br_a')
        with open(opj(rep.work_tree, 'test1'), 'w') as f:
            f.write('a\nb\nc\n\d2')
        rep.call('commit -a -mtest_merge2', _env=ENV_FOR_GIT)
        parent1 = rep.sha(rep.head())
        rep.call('checkout master')
        with open(opj(rep.work_tree, 'test1'), 'w') as f:
            f.write('a1\nb\nc\n\d')
        rep.call('commit -a -mtest_merge3', _env=ENV_FOR_GIT)
        parent2 = rep.sha(rep.head())
        rep.call('merge br_a', _env=ENV_FOR_GIT)
        cmt = rep.cat(rep.head())
        assert set(cmt['parent']) == set([parent1, parent2])

    def test_two_commits(self):
        rep = self._repo()
        self._add_file(rep, 'test1', commit_msg='msg1')
        self._add_file(rep, 'test2', commit_msg='msg2')
        log = list(rep.logs())
        assert len(log) == 2
        assert log[0]['sha']
        assert log[0]['message'] == 'msg2'  # Beware, reverse time
        assert log[1]['message'] == 'msg1'

    def test_empty_log(self):
        rep = self._repo()
        log = rep.logs()
        assert log == []

    def test_cat_tree(self):
        rep = self._repo()
        self._add_file(rep, 'test1', commit_msg='msg1')
        self._add_file(rep, 'test2', commit_msg='msg2')
        assert rep.head()
        tree_sha = rep.cat(rep.head())['tree']
        tree = rep.cat(tree_sha)
        assert tree[0]['path'] == 'test1'
        assert tree[1]['path'] == 'test2'

    def test_cat_blob(self):
        rep = self._repo()
        fn = 'test1'
        content = 'abcd'
        self._add_file(rep, fn, commit_msg='msg1', content=content)
        sha = rep.call('rev-parse HEAD:%s' % fn)
        assert rep.cat(sha) == content

    def test_cat_tag(self):
        rep = self._repo()
        self._add_file(rep, 'test1', commit_msg='msg1', content='abcd')
        tag = 'v1.2.3'
        rep.call(['tag', tag, '-m', 'testtag'], _env=ENV_FOR_GIT)
        assert rep.call('tag') == tag
        tag_sha = rep.call(['rev-parse', tag])
        tag_obj = rep.cat(tag_sha)
        assert tag_obj['type'] == 'commit'
        assert tag_obj['message'] == 'testtag'
        assert tag_obj['tag'] == tag

    def test_cat_blob_with_trailing_spaces(self):
        rep = self._repo()
        fn = 'test1'
        content = '\nabcd \n'
        self._add_file(rep, fn, commit_msg='msg1', content=content)
        sha = rep.call('rev-parse HEAD:%s' % fn)
        assert rep.cat(sha) == content

    def test_cat_blob_with_unicode(self):
        rep = self._repo()
        fn = 'test1'
        content = 'abcd啊呀'
        self._add_file(rep, fn, commit_msg='msg1', content=content)
        sha = rep.call('rev-parse HEAD:%s' % fn)
        assert rep.cat(sha) == content
