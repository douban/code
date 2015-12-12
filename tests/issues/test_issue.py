# encoding: UTF-8

from tests.base import TestCase

from vilya.models.issue import Issue
from vilya.models.issue_comment import IssueComment


class TestIssue(TestCase):

    def test_add_issue(self):
        i = Issue.add('test', 'test description', 'test', 'assignee')
        assert isinstance(i, Issue)
        assert i.title == 'test'
        assert i.description == 'test description'
        assert i.creator_id == 'test'
        assert i.assignee_id == 'assignee'

    def test_update_issue(self):
        i = Issue.add('test', 'test description', 'test', 'assignee')
        i.update("test1", "test1 description")
        i = Issue.get(i.id)
        assert i.title == 'test1'
        assert i.description == 'test1 description'
        assert i.creator_id == 'test'
        assert i.assignee_id == 'assignee'
        assert i.closer_id is None

    def test_close_issue(self):
        i = Issue.add('test', 'test description', 'test', 'assignee')
        i.close("test")
        i = Issue.get(i.id)
        assert i.title == 'test'
        assert i.description == 'test description'
        assert i.creator_id == 'test'
        assert i.closer_id == "test"
        assert i.assignee_id == 'assignee'

    def test_get_issue(self):

        issue1 = Issue.add('test1', 'test1 description', 'test', 'assignee')
        issue2 = Issue.add('test2', 'test2 description', 'test', 'assignee')
        issue2.close("test")

        i1 = Issue.get(issue1.id)
        assert isinstance(i1, Issue)
        assert i1.title == 'test1'
        assert i1.description == 'test1 description'
        assert i1.creator_id == 'test'
        assert i1.assignee_id == 'assignee'
        assert i1.closer_id is None

        i2 = Issue.get(issue2.id)
        assert isinstance(i2, Issue)
        assert i2.title == 'test2'
        assert i2.description == 'test2 description'
        assert i2.creator_id == 'test'
        assert i2.assignee_id == 'assignee'
        assert i2.closer_id == 'test'

        i1 = Issue.get(issue1.id)
        assert isinstance(i1, Issue)
        assert i1.title == 'test1'
        assert i1.description == 'test1 description'
        assert i1.creator_id == 'test'
        assert i1.assignee_id == 'assignee'
        assert i1.closer_id is None

        iss = Issue.gets_by_creator_id("test")
        assert all([isinstance(i, Issue) for i in iss])
        assert len(iss) == 4

        iss = Issue.gets_by_creator_id("test", "open")
        assert all([isinstance(i, Issue) for i in iss])
        assert len(iss) == 4

        iss = Issue.gets_by_creator_id("test", "closed")
        assert all([isinstance(i, Issue) for i in iss])
        assert len(iss) == 2

        iss = Issue.gets_by_assignee_id("assignee")
        assert all([isinstance(i, Issue) for i in iss])
        assert len(iss) == 6

        iss = Issue.gets_by_assignee_id("assignee", "open")
        assert all([isinstance(i, Issue) for i in iss])
        assert len(iss) == 4

        iss = Issue.gets_by_assignee_id("assignee", "closed")
        assert all([isinstance(i, Issue) for i in iss])
        assert len(iss) == 2

        iss = Issue.gets_by_closer_id("test")
        assert all([isinstance(i, Issue) for i in iss])
        assert len(iss) == 2

    def test_add_comment(self):
        i = Issue.add('test', 'test description', 'test', 'assignee')
        c = IssueComment.add(i.id, 'content', 'test')
        assert isinstance(c, IssueComment)
        assert c.issue_id == i.id
        assert c.content == 'content'
        assert c.author_id == 'test'

    def test_get_comment(self):
        i = Issue.add('test', 'test description', 'test', 'assignee')
        c = IssueComment.add(i.id, 'content', 'test')
        c = IssueComment.get(c.id)
        assert isinstance(c, IssueComment)
        assert c.issue_id == i.id
        assert c.content == 'content'
        assert c.author_id == 'test'

        c = IssueComment.add(i.id, 'content', 'test')
        cs = IssueComment.gets_by_issue_id(i.id)
        assert all([isinstance(t, IssueComment) for t in cs])
        assert len(cs) == 2

    def test_update_comment(self):
        i = Issue.add('test', 'test description', 'test', 'assignee')
        c = IssueComment.add(i.id, 'content', 'test')
        c.update('content1')
        c = IssueComment.get(c.id)
        assert c.issue_id == i.id
        assert c.content == 'content1'
        assert c.author_id == 'test'
