# -*- coding: utf-8 -*-

from vilya.libs.template import st
from vilya.models.team import Team
from vilya.views.hub.team import TeamUI

TEAMS_COUNT_PER_PAGE = 10
_q_exports = []


def _q_index(request):
    return TeamsUI()._q_index(request)


def _q_lookup(request, part):
    return TeamUI(request, part)


class TeamsUI(object):
    _q_exports = []

    def _q_index(self, request):
        page = request.get_form_var('page', 1)
        start = TEAMS_COUNT_PER_PAGE * (int(page) - 1)
        teams = Team.gets_by_page(start=start, limit=TEAMS_COUNT_PER_PAGE)
        total_teams = len(Team.gets())
        n_pages = (total_teams - 1) / TEAMS_COUNT_PER_PAGE + 1 if total_teams else 1  # noqa

        return st('/teams/teams.html', **locals())
