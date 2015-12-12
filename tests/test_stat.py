# -*- coding: utf-8 -*-
import os

from vilya.libs.store import store

from tests.base import TestCase
from vilya.models.statistics import (
    get_all_project, get_all_gist, get_all_issue,
    get_issue_comment_count, get_all_ticket,
    get_ticket_comment_count)

from vilya.models.project import CodeDoubanProject
from vilya.models.issue import Issue
from vilya.models.issue_comment import IssueComment
from vilya.models.pull import PullRequest
from vilya.models.ticket import Ticket
from nose.tools import ok_
from vilya.libs.permdir import get_repo_root
from tests.utils import mkdtemp, setup_repos


class TestStat(TestCase):

    def test_project_stat(self):
        store.execute("delete from codedouban_projects where project_id < 5")
        project_rs = get_all_project()
        assert len(project_rs) == 0
        project_fork_count = len(filter(lambda x: x[1] is not None,
                                        project_rs))
        assert project_fork_count == 0

        project_name = "project"
        project = CodeDoubanProject.add(
            project_name, owner_id="test1", summary="test", product="fire")
        git_path = os.path.join(get_repo_root(), '%s.git' % project_name)
        ok_(os.path.exists(git_path))
        project_rs = get_all_project()
        assert len(project_rs) == 1
        project_fork_count = len(filter(lambda x: x[1] is not None,
                                        project_rs))
        assert project_fork_count == 0

        project_fork = project.fork('project_test_fork', 'test_fork')
        project_rs = get_all_project()
        assert len(project_rs) == 2
        project_fork_count = len(filter(lambda x: x[1] is not None,
                                        project_rs))
        assert project_fork_count == 1

        project.delete()
        project_fork.delete()

    def test_gist_stat(self):
        store.execute("delete from gists where id < 20")
        gist_rs = get_all_gist()
        assert len(gist_rs) == 0
        g1 = self._add_gist()
        gist_rs = get_all_gist()
        assert len(gist_rs) == 1
        user_id = "testuser"
        g1.fork(user_id)
        gist_rs = get_all_gist()
        assert len(gist_rs) == 2
        assert len(filter(lambda x: x[1] != 0, gist_rs)) == 1

    def test_issue_stat(self):
        issue_rs = get_all_issue()
        store.execute("delete from issues where id < 20")
        assert len(issue_rs) == 0
        issue_open_count = len(filter(lambda x: x[1] is None, issue_rs))
        assert issue_open_count == 0
        assert len(issue_rs) - issue_open_count == 0

        i1 = Issue.add('test1', 'test des1', 'testuser1', 'assignee')
        issue_rs = get_all_issue()
        assert len(issue_rs) == 1
        issue_open_count = len(filter(lambda x: x[1] is None, issue_rs))
        assert issue_open_count == 1
        assert len(issue_rs) - issue_open_count == 0

        i2 = Issue.add('test2', 'test des1', 'testuser1', 'assignee')
        i3 = Issue.add('test3', 'test des1', 'testuser2', 'assignee')
        issue_rs = get_all_issue()
        assert len(issue_rs) == 3
        issue_open_count = len(filter(lambda x: x[1] is None, issue_rs))
        assert issue_open_count == 3
        assert len(issue_rs) - issue_open_count == 0

        i1.close('testuser1')
        issue_rs = get_all_issue()
        assert len(issue_rs) == 3
        issue_open_count = len(filter(lambda x: x[1] is None, issue_rs))
        assert issue_open_count == 2
        assert len(issue_rs) - issue_open_count == 1

        issue_comment_count = get_issue_comment_count()
        assert issue_comment_count == 0
        IssueComment.add(i2.id, 'content', 'test')
        IssueComment.add(i3.id, 'content', 'test1')
        issue_comment_count = get_issue_comment_count()
        assert issue_comment_count == 2

    def test_pr_stat(self):
        TestCase.setUp(self)
        _, self.proj1, _, self.proj1_fork = setup_repos(
            mkdtemp(), 'testproject1')
        _, self.proj2, _, self.proj2_fork = setup_repos(
            mkdtemp(), 'testproject2')
        pr_rs = get_all_ticket()
        assert len(pr_rs) == 0
        pr_open_count = len(filter(lambda x: x[1] is None, pr_rs))
        assert pr_open_count == 0
        assert len(pr_rs) - pr_open_count == 0

        pullreq1 = PullRequest.open(
            self.proj1_fork, 'master', self.proj1, 'master')
        ticket1 = Ticket.add(self.proj1.id, 'title', 'content', 'testuser')
        pullreq1 = pullreq1.insert(ticket1.ticket_number)
        pullreq2 = PullRequest.open(
            self.proj2_fork, 'master', self.proj2, 'master')
        ticket2 = Ticket.add(self.proj2.id, 'title', 'content', 'testuser')
        pullreq2 = pullreq2.insert(ticket2.ticket_number)
        pr_rs = get_all_ticket()
        assert len(pr_rs) == 2
        pr_open_count = len(filter(lambda x: x[1] is None, pr_rs))
        assert pr_open_count == 2
        assert len(pr_rs) - pr_open_count == 0

        ticket1.close("testuser")
        pr_rs = get_all_ticket()
        assert len(pr_rs) == 2
        pr_open_count = len(filter(lambda x: x[1] is None, pr_rs))
        assert pr_open_count == 1
        assert len(pr_rs) - pr_open_count == 1

        pr_comment_count = get_ticket_comment_count()
        assert(pr_comment_count) == 0
        ticket2.add_comment("comment1", "testuse1")
        ticket2.add_comment("comment2", "testuse2")
        pr_comment_count = get_ticket_comment_count()
        assert(pr_comment_count) == 2
