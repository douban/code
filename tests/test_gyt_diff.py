# -*- coding: utf-8 -*-
import shutil
import tempfile
from os.path import join as opj

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

    def tearDown(self):
        shutil.rmtree(self._gd)
        shutil.rmtree(self._wt)
        shutil.rmtree(self._gd2)
        shutil.rmtree(self._wt2)

    def test_one_diff(self):
        rep = self._repo()
        fn1 = 'test1'
        content1a = 'a\nb\nc\nd'
        content1b = 'a\nb\ncxxx\nd'
        self._add_file(rep, fn1, commit_msg='msg1a', content=content1a)
        sha = rep.sha()
        self._add_file(rep, fn1, commit_msg='msg1b', content=content1b)
        d = rep.diff(sha)
        assert len(d) == 1
        d1 = d[0]
        assert d1['filename'] == fn1
        assert d1['amode'] == d1['bmode'] == '100644'
        assert len(d1['patch']) == 1
        assert d1['patch'][0][0] == '@@ -1,4 +1,4 @@'
        chunk = d1['patch'][0][1]
        assert chunk == [
            ('idem', u'a'),
            ('idem', u'b'),
            ('rem', u'c'),
            ('add', u'cxxx'),
            ('idem', u'd'),
            ('other', u' No newline at end of file')
        ]

    def test_one_diff_without_patch(self):
        rep = self._repo()
        fn1 = 'test1'
        content1a = 'a\nb\nc\nd'
        content1b = 'a\nb\ncxxx\nd'
        self._add_file(rep, fn1, commit_msg='msg1a', content=content1a)
        sha = rep.sha()
        self._add_file(rep, fn1, commit_msg='msg1b', content=content1b)
        d = rep.diff(sha, patch=False)
        assert 'patch' not in d[0]

    def test_one_diff_without_parsing_patch(self):
        rep = self._repo()
        fn1 = 'test1'
        content1a = 'a\nb\nc\nd'
        content1b = 'a\nb\ncxxx\nd'
        self._add_file(rep, fn1, commit_msg='msg1a', content=content1a)
        sha = rep.sha()
        self._add_file(rep, fn1, commit_msg='msg1b', content=content1b)
        d = rep.diff(sha, parse_patch=False)
        chunk = d[0]['patch'][0][1]
        assert chunk == [' a', ' b', '-c', '+cxxx', ' d',
                         '\\ No newline at end of file']

    def test_diff_when_only_one_commit(self):
        rep = self._repo()
        fn1 = 'test1'
        fn2 = 'test2'
        content1a = 'a'
        self._add_file(rep, fn1, commit_msg='msg1a', content=content1a)
        sha = rep.sha()
        self._add_file(rep, fn2, commit_msg='msg1a', content=content1a)
        d = rep.diff(sha)
        assert d[0]['patch'][0][1][0] == ('add', u'a')

    def test_diff_when_on_first_commit(self):
        rep = self._repo()
        fn1 = 'test1'
        content1a = 'a'
        self._add_file(rep, fn1, commit_msg='msg1a', content=content1a)
        d = rep.diff()
        assert d[0]['patch'][0][1][0] == ('add', u'a')

    def test_two_diffs(self):
        rep = self._repo()
        fn1 = 'test1'
        fn2 = 'test2'
        content1a = 'a\nb\nc\nd'
        content1b = 'a\nb\ncxxx\nd'
        content2a = '1\n2\n3\n4'
        content2b = '1\n2xxx\n3\n4'
        self._add_file(rep, fn1, commit_msg='msg1a', content=content1a)
        self._add_file(rep, fn2, commit_msg='msg2a', content=content2a)
        sha = rep.sha()
        self._add_file(rep, fn1, commit_msg='msg1b', content=content1b)
        self._add_file(rep, fn2, commit_msg='msg2b', content=content2b)
        d = rep.diff(sha)
        assert len(d) == 2
        assert d[0]['filename'] == fn1
        assert d[1]['filename'] == fn2

    def test_diff_with_one_rename(self):
        rep = self._repo()
        content1a = 'aaaaa'
        self._add_file(
            rep, 'test_filename', commit_msg='msg1a', content=content1a)
        rep.call('mv test_filename test_new_filename')
        rep.call('commit -mmv', _env=ENV_FOR_GIT)
        d = rep.diff()
        assert len(d) == 2, "should have two patches if undetected rename"
        d = rep.diff(rename_detection=True)
        assert len(d) == 1, "should have one patch if undetected rename"
        assert d[0]['filename'] == 'test_filename'
        assert d[0]['new_filename'] == 'test_new_filename'

    def test_diff_with_two_renames(self):
        rep = self._repo()
        self._add_file(
            rep, 'test_filename1', commit_msg='msg1a', content='aaaaa')
        self._add_file(
            rep, 'test_filename2', commit_msg='msg2a', content='bbbbb')
        rep.call('mv test_filename1 test_new_filename1')
        rep.call('mv test_filename2 test_new_filename2')
        rep.call('commit -mmv', _env=ENV_FOR_GIT)
        d = rep.diff()
        assert len(d) == 4, "should have 4 patches if undetected rename, had %s" % len(d)  # noqa
        d = rep.diff(rename_detection=True)
        assert len(d) == 2, "should have 2 patch if undetected rename"
        print d
        assert d[0]['filename'] == 'test_filename1'
        assert d[0]['new_filename'] == 'test_new_filename1'
        assert d[1]['filename'] == 'test_filename2'
        assert d[1]['new_filename'] == 'test_new_filename2'
