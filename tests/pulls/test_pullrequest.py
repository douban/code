# -*- coding: utf-8 -*-

from tests.base import TestCase
from vilya.models.pull import PullRequest
from vilya.models.ticket import PRCounter, Ticket
from tests.utils import mkdtemp, setup_repos, delete_project


class PullRequestTest(TestCase):

    def setUp(self):
        TestCase.setUp(self)
        for name in ('testproject1', 'testproject2', 'testproject1_fork',
                     'testproject2_fork'):
            delete_project(name)
        _, self.proj1, _, self.proj1_fork = setup_repos(mkdtemp(),
                                                        'testproject1')
        _, self.proj2, _, self.proj2_fork = setup_repos(mkdtemp(),
                                                        'testproject2')

    def test_incr_counter(self):
        count = PRCounter.incr(self.proj1.id)
        assert count == 1
        count = PRCounter.incr(self.proj1.id)
        assert count == 2
        count = PRCounter.incr(self.proj2.id)
        assert count == 1

    def test_pullrequest(self):
        pullreq1 = PullRequest.open(
            self.proj1_fork, 'master', self.proj1, 'master')
        ticket1 = Ticket.add(self.proj1.id, 'title', 'content', 'testuser')
        pullreq1.insert(ticket1.ticket_number)

        pullreq2 = PullRequest.open(
            self.proj2_fork, 'master', self.proj2, 'master')
        ticket2 = Ticket.add(self.proj2.id, 'title', 'content', 'testuser')
        pullreq2.insert(ticket2.ticket_number)

        opened_prs = self.proj1_fork.open_parent_pulls
        assert len(opened_prs) == 1

        opened_prs = self.proj2_fork.open_parent_pulls
        assert len(opened_prs) == 1

        ticket1.close('testuser')
        opened_prs = self.proj1_fork.open_parent_pulls
        assert len(opened_prs) == 0

        ticket2.close('testuser')
        opened_prs = self.proj2_fork.open_parent_pulls
        assert len(opened_prs) == 0
