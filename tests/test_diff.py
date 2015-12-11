# -*- coding: utf-8 -*-

import os
import shutil

from vilya.models.project import CodeDoubanProject
from vilya.models import git

from tests.base import TestCase

from vilya.libs import gyt
from vilya.libs.diff import rehunk, linehtml
from vilya.libs.permdir import get_repo_root

a_hunk = [('idem', u'/* highlight style */'), ('rem', u'.highlight { color: #008000; font-weight: bold; } /* Keyword */'), ('add', u'.highlight .hll { background-color: #ffffcc; }'), ('add', u'.highlight  { background: #ffffff; }'), ('add', u'.highlight .c { color: #808080; } /* Comment */'), ('add', u'.highlight .err { color: #F00000; background-color: #F0A0A0; } /* Error */'), ('add', u'.highlight .k { color: #008000; font-weight: bold; } /* Keyword */'), ('idem', u'.highlight .o { color: #303030; } /* Operator */'), ('idem', u'.highlight .cm { color: #808080; } /* Comment.Multiline */'), ('idem', u'.highlight .cp { color: #507090; } /* Comment.Preproc */')]  # noqa


class TestDiff(TestCase):
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
            if os.path.exists(git_path):
                shutil.rmtree(git_path, ignore_errors=True)
            try:
                os.mkdir(work_tree_path)
            except OSError:
                pass
        CodeDoubanProject.create_git_repo(git_path)
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

    def test_diff(self):
        repo = self._repo('test_diff', bare=False)
        c1_sha = self._commit(repo, 'testfile', 'content1', 'msg1')
        c2_sha = self._commit(repo, 'testfile', 'content2', 'msg2')
        diffs = repo.get_3dot_diff(c1_sha, c2_sha)
        assert len(diffs) == 1, "Should be only one diff"
        diff = diffs[0]
        assert len(diff.chunks) == 1, "The diff has only one chunk"
        chunk = diff.chunks[0]
        assert ('rem', u'-content\x00^1\x01') in chunk.diff_lines, \
            "diff should contain content1 removal"
        assert ('add', u'+content\x00^2\x01') in chunk.diff_lines, \
            "diff should contain content2 added"

    def test_diff_one_file(self):
        repo = self._repo('test_diff_one_file', bare=False)
        c1_sha = self._commit(repo, 'testfile', 'content1', 'msg1')
        c2_sha = self._commit(repo, 'testfile', 'content2', 'msg2')
        diffs = repo.get_3dot_diff_onefile(c1_sha, c2_sha, 'testfile')
        assert len(diffs) == 1, "Should be only one diff"
        diff = diffs[0]
        assert len(diff.chunks) == 1, "The diff has only one chunk"
        chunk = diff.chunks[0]
        assert ('rem', u'-content\x00^1\x01') in chunk.diff_lines, \
            "diff should contain content1 removal"
        assert ('add', u'+content\x00^2\x01') in chunk.diff_lines, \
            "diff should contain content2 added"

    def test_diff_one_file_with_lines_starting_with_minus(self):
        repo = self._repo('test_diff_one_file', bare=False)
        c1_sha = self._commit(
            repo, 'testfile', '-a\n-test\n-c\n\ncontent1', 'msg1')
        c2_sha = self._commit(
            repo, 'testfile', '-a\n-test\n-c\n\ncontent2', 'msg2')
        diffs = repo.get_3dot_diff_onefile(c1_sha, c2_sha, 'testfile')
        assert len(diffs) == 1, "Should be only one diff"
        diff = diffs[0]
        assert len(diff.chunks) == 1, "The diff has only one chunk"
        assert ('deletion', '2', ' ', u'-test') not in diff.diff_content
        assert ('normal', '2', '2', u' -test') in diff.diff_content

    def test_parse_merge_diff_empty(self):
        repo = self._repo('test_merge_diff', bare=False)
        self._commit(repo, 'testfile', 'msg')
        not_bare = gyt.repo(repo.path, repo.work_tree)
        assert not not_bare.is_bare()
        self._commit(repo, 'tf1', 'content1', 'msg1')
        not_bare.call('checkout -b test_br')
        sha2 = self._commit(repo, 'tf2', 'content2', 'msg2')
        not_bare.call('checkout master')
        sha3 = self._commit(repo, 'tf3', 'content3', 'msg3')
        not_bare.call('merge test_br', _env=self.env_for_git)
        sha_merge = repo.pygit2_repo.revparse_single('HEAD').hex
        diff = repo.parse_diff(sha_merge)
        assert diff['body'] == ''
        assert len(diff['difflist']) == 1
        assert diff['parents'] == '%s %s' % (sha3, sha2)

    def test_hunk(self):
        hunk = rehunk(a_hunk)
        assert hunk == [('idem', u' /* highlight style */'), ('rem', u'-.highlight { color: #008000; font-weight: bold; } /* Keyword */'), ('add', u'+.highlight .hll { background-color: #ffffcc; }'), ('add', u'+.highlight  { background: #ffffff; }'), ('add', u'+.highlight .c { color: #808080; } /* Comment */'), ('add', u'+.highlight .err { color: #F00000; background-color: #F0A0A0; } /* Error */'), ('add', u'+.highlight \x00+.k \x01{ color: #008000; font-weight: bold; } /* Keyword */'), ('idem', u' .highlight .o { color: #303030; } /* Operator */'), ('idem', u' .highlight .cm { color: #808080; } /* Comment.Multiline */'), ('idem', u' .highlight .cp { color: #507090; } /* Comment.Preproc */')]  # noqa

    def test_color(self):
        diff = 'background-color: #3aa253;'
        html = 'background-color: <span class="color" data-color="#3aa253">#3aa253</span>;'  # noqa
        result = linehtml(diff)
        assert result == html

    def test_diff_smart_slice(self):
        repo = self._repo('test_diff_smart_slice.txt', bare=False)
        content1 = 'a\n' * 100
        content2 = 'a\n' * 5 + 'b\n' * 10 + 'a\n' * 20 + 'b\n' * 40
        c1_sha = self._commit(repo, 'testfile', content1, 'msg1')
        c2_sha = self._commit(repo, 'testfile', content2, 'msg2')
        diffs = repo.get_3dot_diff(c1_sha, c2_sha)
        diff = diffs[0]
        content = diff.diff_content

        normal_slice1 = content[:11]
        smart_slice1 = diff.smart_slice(10)
        assert smart_slice1[-1] == normal_slice1[-1]
        assert len(smart_slice1) == len(normal_slice1) and len(smart_slice1) <= 15  # noqa

        normal_slice2 = content[:31]
        smart_slice2 = diff.smart_slice(30)

        assert smart_slice2[-1] == normal_slice2[-1]
        assert len(smart_slice2) < len(normal_slice2)
        assert len(smart_slice2) <= 25
        assert smart_slice2[0][0] == 'tips'

        normal_slice3 = content[:101]
        smart_slice3 = diff.smart_slice(100)

        assert len(smart_slice3) <= 25
        assert len(smart_slice3) < len(normal_slice3)
        assert smart_slice3[-1] == normal_slice3[-1]
        assert smart_slice3[0][0] != 'tips'
