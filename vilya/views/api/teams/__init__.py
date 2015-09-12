# -*- coding: utf-8 -*-
from vilya.views.api.team import TeamUI

_q_exports = []


def _q_lookup(request, name):
    return TeamUI(name)


def _q_access(request):
    request.response.set_content_type('application/json; charset=utf-8')
