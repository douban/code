# encoding: UTF-8

import os
from os.path import join
from contextlib import contextmanager

from nose.tools import eq_, ok_

from vilya.models.pull import PullRequest
from vilya.libs import gyt
from tests.base import TestCase
from tests.utils import mkdtemp, chdir, clone, setup_repos, setup2repos
from vilya.models.user import User


class TestPullRequest(TestCase):

    def setUp(self):
        TestCase.setUp(self)

    @contextmanager
    def clone_clean(self, git_dir):
        with mkdtemp() as work_path:
            gyt.call(['git', 'clone', git_dir, work_path])
            assert os.path.exists(join(work_path, '.git'))
            yield work_path

    def test_is_auto_mergable_should_not_commit_merge(self):
        """调用 is_auto_mergable() 不应该导致仓库被 merge """
        with setup2repos('prj1') as \
                (path, repo, fork_path, fork_repo):
            pullreq = PullRequest.open(fork_repo, 'master', repo, 'master')
            ok_(pullreq.is_auto_mergable())

            with self.clone_clean(path) as workdir:
                assert not os.path.exists(join(workdir, 'a'))

    def test_conflict_detection(self):
        """有冲突存在时，is_auto_mergable()应返回False"""
        with mkdtemp() as tmpdir:
            path, repo, fork_path, fork_repo = setup_repos(
                tmpdir, 'test_conflict_detection')

            # make conflict changes

            with clone(path) as work_path:
                with open(join(work_path, 'a'), 'w') as f:
                    f.write("asdf")

            with clone(fork_path) as work_path:
                with open(join(work_path, 'a'), 'w') as f:
                    f.write("fdsa")

            # submit a pull request

            pullreq = PullRequest.open(fork_repo, 'master', repo, 'master')
            assert not pullreq.is_auto_mergable()
            # assure merge --abort
            assert not os.path.exists(os.path.join(path, 'MERGE_MODE'))

    def test_merge(self):
        """merge()应该将远程代码合并到bare仓库中"""

        with setup2repos('prj_merge') as (path, repo, fork_path, fork_repo):

            pullreq = PullRequest.open(fork_repo, 'master', repo, 'master')
            u = User('testmerge')
            pullreq.merge(u)

            with self.clone_clean(path) as work_path:
                content = open(join(work_path, 'a')).read()
                eq_(content, "a_hunk = [('idem', u'/* highlight style */'), ('rem', u'.highlight { color: #008000; font-weight: bold; } /* Keyword */'), ('add', u'.highlight .hll { background-color: #ffffcc; }'), ('add', u'.highlight  { backggggground: #ffffff; }'), ('add', u'.high .c { color: #808080; } /* Coomment */'), ('add', u'.highlight .err { color: #F00000; background-color: #F00A0A0; } /* Error */'), ('add', u'.highlight .k { color: #008000; font-weight: bold; } /* Keyword */'), ('idem', u'.highlight .o { color: #303; } /* Operator ****/'), ('idem', u'.highlight .cm { color: #808080; } /* Comment.Multiline */'),('idem', u'adfadsfadsf'),  ('idem', u'.highlight .cp { color: #507090; } /* Comment.Preproc */')]\n")  # noqa

    def test_is_up_to_date(self):
        """应该能探测是否是已经merge过的"""
        with setup2repos('prj_uptodate') as (path, repo, fork_path, fork_repo):

            with self.clone_clean(path) as work_path:
                with chdir(work_path):
                    gyt.call(['git', 'pull', fork_path])
                    gyt.call(['git', 'push', 'origin', 'master'])

            pullreq = PullRequest.open(fork_repo, 'master', repo, 'master')
            ok_(pullreq.is_up_to_date())

    def test_get_commits(self):
        """应该能够得到所有将合并的改动"""
        with setup2repos('prj3') as (path, repo, fork_path, fork_repo):

            pullreq = PullRequest.open(fork_repo, 'master', repo, 'master')
            commits = pullreq.commits
            eq_(len(commits), 1)

    def test_get_diffs(self):
        """应该能够得到所有将合并的diff"""
        with setup2repos('prj4') as (path, repo, fork_path, fork_repo):

            # make some change in origin repo, too
            with clone(path) as work_path:
                with chdir(work_path):
                    with open('b', 'w') as f:
                        f.write('b')

            pullreq = PullRequest.open(fork_repo, 'master', repo, 'master')
            diffs = pullreq.get_diff()
            # should not contain file b in origin
            eq_(diffs.length, 1)

    def test_get_merge_base(self):
        """应该能够得到merge_base，即from_sha、to_sha的最近公共父commit sha"""
        with setup2repos('prj5') as (path, repo, fork_path, fork_repo):
            pullreq = PullRequest.open(fork_repo, 'master', repo, 'master')
            merge_base = pullreq.merge_base
            assert merge_base is not None
