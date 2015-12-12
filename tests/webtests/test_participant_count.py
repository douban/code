# encoding: utf-8
from tests.base import TestCase
from webtest import TestApp

from vilya.models.project import CodeDoubanProject
from vilya.models.team import Team
from vilya.models.project_issue import ProjectIssue
from vilya.models.team_issue import TeamIssue
from tests.utils import delete_project
import app as M


class ParticipantCountTest(TestCase):
    def test_new_project_issue_participant_count(self):
        app = TestApp(M.app)
        project_name = "project"
        delete_project(project_name)
        project = CodeDoubanProject.add(
            project_name, owner_id="test1", summary="test", product="fire")
        issue = ProjectIssue.add(
            'test', 'test description', 'test', project=project.id)
        resp = app.get(issue.url)

        assert resp.status_int == 200
        assert 'Issues' in resp.body
        assert '<strong>1</strong> participant' in resp.text
        assert '<strong>1</strong> participants' not in resp.text

    def test_new_team_issue_participant_count(self):
        app = TestApp(M.app)
        for team in Team.gets():
            if team:
                team.delete()
        team = Team.add("test_team", "test team", "test")
        issue = TeamIssue.add('test', 'test description', 'test', team=team.id)
        resp = app.get(issue.url)

        assert resp.status_int == 200
        assert 'Issues' in resp.body
        assert '<strong>1</strong> participant' in resp.text
        assert '<strong>1</strong> participants' not in resp.text
