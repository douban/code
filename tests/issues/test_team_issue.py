# encoding: UTF-8

from tests.base import TestCase

from vilya.models.team_issue import TeamIssue


class TestTeamIssue(TestCase):

    def test_add_issue(self):
        t = TeamIssue.add('test', 'test description', 'test', team=1)
        assert isinstance(t, TeamIssue)
        assert t.title == 'test'
        assert t.description == 'test description'
        assert t.team_id == 1
        t.delete()

    def test_get_issue(self):
        TeamIssue.add('test1', 'test1 description', 'test', team=1)
        TeamIssue.add('test2', 'test2 description', 'test', team=1)
        TeamIssue.add('test3', 'test3 description', 'test', team=1)
        TeamIssue.add('test4', 'test4 description', 'test', team=2)

        rs = TeamIssue.gets_by_target(1)
        assert all([isinstance(i, TeamIssue) for i in rs])
        assert len(rs) == 3
