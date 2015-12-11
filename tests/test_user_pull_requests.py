# -*- coding: utf-8 -*-
import time

from tests.base import TestCase

from vilya.models.user import User
from vilya.models.project import CodeDoubanProject
from vilya.models.ticket import Ticket
from tests.utils import delete_project


class TestUserPullRequests(TestCase):

    def setUp(self):
        TestCase.setUp(self)
        delete_project('test_pr1')
        delete_project('test_pr2')
        self.proj1 = CodeDoubanProject.add('test_pr1', owner_id='test')
        self.proj2 = CodeDoubanProject.add('test_pr2', owner_id='test')

    def test_get_user_pull_requests(self):
        u = User('testu%s' % time.time())
        title = 'test title'
        desc = 'test desc'
        t1 = Ticket.add(self.proj1.id, title, desc, u.username)

        assert u.get_invited_pull_requests() == []
        u.add_invited_pull_request(t1.id)
        print u.get_invited_pull_requests()
        assert u.get_invited_pull_requests()[0].id == t1.id
        assert u.n_open_invited == 1

        assert u.get_participated_pull_requests()[0].id == t1.id
        u.add_participated_pull_request(t1.id)
        assert u.get_participated_pull_requests()[0].id == t1.id
        assert u.n_open_participated == 1

    def test_get_user_submitted_pull_requests(self):
        title = 'test title'
        desc = 'test desc'
        u = User('testu%s' % time.time())
        p1_t1 = Ticket.add(self.proj2.id, title, desc, u.username)
        assert u.get_user_submit_pull_requests() != []
        assert u.n_user_open_submit_pull_requests == 1

        p1_t1.close('testuser')
        assert u.get_user_submit_pull_requests() == []
        assert u.n_user_open_submit_pull_requests == 0

        assert u.n_open_pull_requests == 0
