# encoding: UTF-8

from tests.base import TestCase

from vilya.models.issue import Issue
from vilya.models.project_issue import ProjectIssue


class TestProjectIssue(TestCase):

    def test_add_issue(self):
        p = ProjectIssue.add('test', 'test description', 'test', project=1)
        assert isinstance(p, ProjectIssue)
        assert p.title == 'test'
        assert p.description == 'test description'
        assert p.project_id == 1
        p.delete()

    def test_get_issue(self):
        p = ProjectIssue.add('test', 'test description', 'test', project=1)
        r = ProjectIssue.get(p.project_id, issue_id=p.issue_id)
        assert isinstance(r, ProjectIssue)
        assert r.project_id == 1

        r = ProjectIssue.get(p.project_id, number=p.number)
        assert isinstance(r, ProjectIssue)
        assert r.project_id == 1

        r = Issue.get_cached_issue(p.issue_id)
        assert isinstance(r, ProjectIssue)
        assert r.title == 'test'
        assert r.description == 'test description'
        assert r.project_id == 1

        p2 = ProjectIssue.add(
            'test2', 'test2 description', 'test', project=1,
            assignee='assignee')
        p3 = ProjectIssue.add(
            'test3', 'test3 description', 'test', project=1,
            assignee='assignee')
        p4 = ProjectIssue.add(
            'test4', 'test4 description', 'test', project=1, assignee='test')
        p5 = ProjectIssue.add(
            'test5', 'test5 description', 'test1', project=2, assignee='test')

        rs = ProjectIssue._gets_by_project_id(1)
        assert len(rs) == 4

        rs = ProjectIssue._get_issues_by_project_id(1)
        assert all([isinstance(i, ProjectIssue) for i in rs])
        assert len(rs) == 4

        rs = ProjectIssue.gets_by_assignee_id(1, 'assignee')
        assert all([isinstance(i, ProjectIssue) for i in rs])
        assert len(rs) == 2

        rs = ProjectIssue.gets_by_creator_id(1, 'test')
        assert all([isinstance(i, ProjectIssue) for i in rs])
        assert len(rs) == 4

        for p in [p, p2, p3, p4, p5]:
            p.delete()

    def test_n_issue(self):
        p1 = ProjectIssue.add(
            'test1', 'test1 description', 'test', project=1,
            assignee='assignee')
        p1.close('test')
        p2 = ProjectIssue.add(
            'test2', 'test2 description', 'test', project=1,
            assignee='assignee')
        p2.close('test')
        p3 = ProjectIssue.add(
            'test3', 'test3 description', 'test', project=1,
            assignee='assignee')
        p4 = ProjectIssue.add(
            'test4', 'test4 description', 'test', project=1,
            assignee='test')
        p5 = ProjectIssue.add(
            'test5', 'test5 description', 'test1', project=2,
            assignee='test')

        count = ProjectIssue.get_count_by_project_id(1)
        assert count == 4
        count = ProjectIssue.get_count_by_project_id(1, 'open')
        assert count == 2
        count = ProjectIssue.get_count_by_project_id(1, 'closed')
        assert count == 2

        count = ProjectIssue.get_count_by_assignee_id(1, 'assignee')
        assert count == 3
        count = ProjectIssue.get_count_by_assignee_id(1, 'assignee', 'open')
        assert count == 1
        count = ProjectIssue.get_count_by_assignee_id(1, 'assignee', 'closed')
        assert count == 2

        count = ProjectIssue.get_count_by_creator_id(1, 'test')
        assert count == 4
        count = ProjectIssue.get_count_by_creator_id(1, 'test', 'open')
        assert count == 2
        count = ProjectIssue.get_count_by_creator_id(1, 'test', 'closed')
        assert count == 2

        r = ProjectIssue.get(p1.project_id, p1.issue_id)
        assert isinstance(r, ProjectIssue)
        assert r.n_closed_issues == 2
        assert r.n_open_issues == 2

        for p in [p1, p2, p3, p4, p5]:
            p.delete()

    def test_open_and_close_issue(self):
        p1 = ProjectIssue.add('test1', 'test1 description', 'test', project=1)
        p2 = ProjectIssue.add('test2', 'test2 description', 'test', project=1)
        p3 = ProjectIssue.add('test3', 'test3 description', 'test', project=1)

        count = ProjectIssue.get_count_by_project_id(1)
        assert count == 3
        p1.close('test')
        count = ProjectIssue.get_count_by_project_id(1, 'open')
        assert count == 2
        p1.open()
        count = ProjectIssue.get_count_by_project_id(1, 'open')
        assert count == 3

        for p in [p1, p2, p3]:
            p.delete()

    def test_add_tags(self):
        target_id = project_id = 1
        p = ProjectIssue.add(
            'test', 'test description', 'test', project=project_id)
        assert isinstance(p, ProjectIssue)
        assert p.title == 'test'
        assert p.description == 'test description'
        assert p.project_id == 1

        tags = ['tag1', 'tag2', 'tag3']

        p.add_tags(tags, target_id)
        assert len(p.tags) == len(tags)

        tag_names = [t.name for t in p.tags]
        assert set(tags) & set(tag_names) == set(tags)
        p.delete()

    def test_gets_by_issue_ids(self):
        project_id = 1
        p = ProjectIssue.add(
            'test', 'test description', 'test', project=project_id)
        assert isinstance(p, ProjectIssue)
        assert p.title == 'test'
        assert p.description == 'test description'
        assert p.project_id == 1

        project_issues = ProjectIssue._gets_by_issue_ids(
            [p.issue_id], state=None)
        assert len(project_issues) == 1
        pissue = project_issues[0]
        assert isinstance(pissue, ProjectIssue)
        assert pissue.project_id == project_id

        project_issues = ProjectIssue._gets_by_issue_ids(
            [p.issue_id], state="open")
        assert len(project_issues) == 1
        pissue = project_issues[0]
        assert isinstance(pissue, ProjectIssue)
        assert pissue.project_id == project_id

        project_issues = ProjectIssue._gets_by_issue_ids(
            [p.issue_id], state="closed")
        assert len(project_issues) == 0

        pissue.close("test")

        project_issues = ProjectIssue._gets_by_issue_ids(
            [p.issue_id], state="open")
        assert len(project_issues) == 0

        project_issues = ProjectIssue._gets_by_issue_ids(
            [p.issue_id], state="closed")
        assert len(project_issues) == 1
        pissue = project_issues[0]
        assert isinstance(pissue, ProjectIssue)
        assert pissue.project_id == project_id
        p.delete()

    def test_gets_by_project_ids(self):
        p1 = ProjectIssue.add('test1', 'desp', 'test', project=1)
        p2 = ProjectIssue.add('test2', 'desp', 'test2', project=2)
        p3 = ProjectIssue.add('test3', 'desp', 'test3', project=2)

        issues = ProjectIssue.gets_by_project_ids([1, 2])

        assert len(issues), 3
        for p in [p1, p2, p3]:
            p.delete()
