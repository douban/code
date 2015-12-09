# -*- coding: utf-8 -*-
from vilya.libs import gyt
import shutil
import tempfile
from os.path import join as opj

from tests.base import TestCase

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
        repo = rep.repo
        ref_cmt1 = repo.revparse_single(sha)
        ref_cmt2 = repo.revparse_single('HEAD')
        diff = ref_cmt1.tree.diff(ref_cmt2.tree)
        patches, filenames = gyt.parse_raw_diff_patches(diff.patch, True)
        assert patches[0][0][1] == [
            ('idem', u'a'),
            ('idem', u'b'),
            ('rem', u'c'),
            ('add', u'cxxx'),
            ('idem', u'd'),
            ('other', u' No newline at end of file')
        ]
