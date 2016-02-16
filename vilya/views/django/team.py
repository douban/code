# -*- coding: utf-8 -*-

from django.http import HttpResponse
from vilya.libs.template import st


def teams(request):
    from vilya.models.team import Team
    TEAMS_COUNT_PER_PAGE = 10
    page = request.GET.get('page', 1)
    start = TEAMS_COUNT_PER_PAGE * (int(page) - 1)
    teams = Team.gets_by_page(start=start, limit=TEAMS_COUNT_PER_PAGE)
    total_teams = len(Team.gets())
    n_pages = (total_teams - 1) / TEAMS_COUNT_PER_PAGE + 1 if total_teams else 1  # noqa

    return HttpResponse(st('/teams/teams.html', **locals()))
