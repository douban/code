# -*- coding: utf-8 -*-

from __future__ import absolute_import
from nose.tools import ok_

from tests.base import TestCase
from vilya.models.team import Team
from vilya.models.nteam import TeamProjectRelationship, TeamUserRelationship
from vilya.libs.text import get_mentions_from_text


class TestTeam(TestCase):

    def test_add_and_delete_team(self):
        team_id = "test_team"
        team_name = "测试team"
        description = "测试"
        n_team = len(Team.gets())
        team = Team.add(team_id, team_name, description)
        new_n_team = len(Team.gets())
        ok_(new_n_team == n_team + 1)
        ok_(team_id == team.uid)
        team.delete()
        new_n_team = len(Team.gets())
        ok_(new_n_team == n_team)

    def test_add_and_delete_team_user_relationship(self):
        team_id = 1111
        user_id = "chengeng"
        identity = 2
        rl = TeamUserRelationship.create(team_id=team_id,
                                         user_id=user_id,
                                         identity=identity)
        relationship = TeamUserRelationship.get(team_id=team_id,
                                                user_id=user_id)
        ok_(rl.id == relationship.id)
        rl.delete()

    def test_add_and_delete_team_project_relationship(self):
        team_id = 2222
        project_id = 33333
        rl = TeamProjectRelationship.create(team_id=team_id,
                                            project_id=project_id)
        relationship = TeamProjectRelationship.get(team_id=team_id,
                                                   project_id=project_id)
        ok_(rl.id == relationship.id)
        rl.delete()

    def test_delete_team_project_relationship_by_project_id(self):
        team_id = 2222
        project_id = 2222
        rl = TeamProjectRelationship.create(team_id=team_id,
                                            project_id=project_id)
        relationship = TeamProjectRelationship.get(team_id=team_id,
                                                   project_id=project_id)
        ok_(rl.id == relationship.id)

        TeamProjectRelationship.deletes(project_id=project_id)
        relationship = TeamProjectRelationship.get(team_id=team_id,
                                                   project_id=project_id)
        ok_(relationship is None)

    def ttest_at_team(self):  # FIXME
        mention = "test_team"
        team_name = "测试team"
        description = "测试"
        team = Team.add(mention, team_name, description)
        ok_(team.uid == mention)

        content = "@test_team code"
        users = get_mentions_from_text(content)
        # ok_(len(users) == 0)

        team_id = team.id
        user_id = "chengeng"
        identity = 2
        rl = TeamUserRelationship.create(team_id=team_id,
                                         user_id=user_id,
                                         identity=identity)
        ok_(rl.user_id == user_id)

        users = get_mentions_from_text(content)
        ok_(users[0] == user_id)

        rl.delete()

        users = get_mentions_from_text(content)
        ok_(len(users) == 0)

        team.delete()

        users = get_mentions_from_text(content)
        ok_(users[0] == mention)
