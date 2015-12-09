# -*- coding: utf-8 -*-

from quixote.errors import TraversalError
from vilya.views.util import jsonize, render_actions
from vilya.models.feed import get_team_feed, PAGE_ACTIONS_COUNT
from vilya.models.team import Team

_q_exports = []

class TeamActionUI(object):
    _q_exports = []

    def __init__(self, team_uid):
        self.team_uid = team_uid

    @jsonize
    def _q_lookup(self, request, num):
        if not num.isdigit():
            raise TraversalError
        num = int(num)
        team = Team.get_by_uid(self.team_uid)
        actions = get_team_feed(team.id).get_actions(start=num,
                                                     stop=num+PAGE_ACTIONS_COUNT-1)
        length = len(actions)
        render_html = render_actions(actions, show_avatar=True)
        return {'result': render_html, 'length': length}


def _q_lookup(request, team_uid):
    return TeamActionUI(team_uid)
