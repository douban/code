# encoding: utf-8
from tests.base import TestCase
from webtest import TestApp

from vilya.models.project import CodeDoubanProject
from vilya.models.project_issue import ProjectIssue
from tests.utils import delete_project
import app as M


class IssuesVotesAndCommentsCountDisplayTest(TestCase):
    def test_zero_vote_and_zero_comment_display(self):
        app = TestApp(M.app)
        project_name = "project"
        delete_project(project_name)
        project = CodeDoubanProject.add(
            project_name, owner_id="test1", summary="test", product="fire")
        ProjectIssue.add('test', 'test description', 'test',
                         project=project.id)
        resp = app.get(project.url + "/issues/")

        assert resp.status_int == 200
        assert 'Issues' in resp.body
        assert '0 vote' not in resp.body
        assert '0 comment' not in resp.body

    def test_one_vote_display(self):
        app = TestApp(M.app)
        project_name = "project1"
        delete_project(project_name)
        project = CodeDoubanProject.add(
            project_name, owner_id="test1", summary="test", product="fire")
        issue = ProjectIssue.add('test', 'test description', 'test',
                                 project=project.id)
        issue.upvote_by_user('test1')

        resp = app.get(project.url + "/issues/")
        assert resp.status_int == 200
        assert "Issues" in resp.body
        assert "1 vote" in resp.body
        assert "1 votes" not in resp.body

    def test_one_comment_display(self):
        app = TestApp(M.app)
        project_name = "project2"
        delete_project(project_name)
        project = CodeDoubanProject.add(
            project_name, owner_id="test1", summary="test", product="fire")
        issue = ProjectIssue.add('test', 'test description', 'test',
                                 project=project.id)
        issue.add_comment('this is a comment', 'test')
        resp = app.get(project.url + "/issues/")

        assert resp.status_int == 200
        assert "Issues" in resp.body
        assert "1 comment" in resp.body
        assert "1 comments" not in resp.body

    def test_two_votes_display(self):
        app = TestApp(M.app)
        project_name = "project3"
        delete_project(project_name)
        project = CodeDoubanProject.add(
            project_name, owner_id="test1", summary="test", product="fire")
        issue = ProjectIssue.add('test', 'test description', 'test',
                                 project=project.id)
        issue.upvote_by_user('test1')
        issue.upvote_by_user('test2')
        resp = app.get(project.url + "/issues/")

        assert resp.status_int == 200
        assert "Issues" in resp.body
        assert "2 votes" in resp.body

    def test_two_comments_display(self):
        app = TestApp(M.app)
        project_name = "project4"
        delete_project(project_name)
        project = CodeDoubanProject.add(
            project_name, owner_id="test1", summary="test", product="fire")
        issue = ProjectIssue.add('test', 'test description', 'test',
                                 project=project.id)
        issue.add_comment('this is a comment', 'test')
        issue.add_comment('this is also a comment', 'test')
        resp = app.get(project.url + "/issues/")

        assert resp.status_int == 200
        assert "Issues" in resp.body
        assert "2 comments" in resp.body
