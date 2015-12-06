# encoding: UTF-8

from tests.base import TestCase

from vilya.libs.store import store

from vilya.models.user_issue import UserIssue
from vilya.models.project_issue import ProjectIssue


class TestUserIssue(TestCase):
    def setUp(self):
        super(TestCase, self).setUp()
        self.clear()

    def tearDown(self):
        self.clear()
        super(TestCase, self).tearDown()

    def clear(self):
        store.execute('delete from issues where 1=1')
        store.execute('delete from project_issues where 1=1')
        store.commit()

    def test_get_issue(self):
        p1 = ProjectIssue.add('test1', 'test1 description', 'test', project=1,
                              assignee='assignee')
        p1.close('test')
        p2 = ProjectIssue.add('test2', 'test2 description', 'test', project=1,
                              assignee='assignee')
        p2.close('test')
        p3 = ProjectIssue.add('test3', 'test3 description', 'test', project=1,
                              assignee='assignee')
        p4 = ProjectIssue.add('test4', 'test4 description', 'test', project=1,
                              assignee='test')
        p5 = ProjectIssue.add('test5', 'test5 description', 'test1', project=2,
                              assignee='test')

        rs = UserIssue.gets_by_creator_id('test', state='open')
        assert all([isinstance(i, ProjectIssue) for i in rs])
        assert len(rs) == 2

        rs = UserIssue.gets_by_assignee_id('test', state='open')
        assert all([isinstance(i, ProjectIssue) for i in rs])
        assert len(rs) == 2
