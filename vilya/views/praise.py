# -*- coding: utf-8 -*-

from __future__ import absolute_import

import json

from vilya.libs.template import st
from vilya.models.recommendation import Recommendation

_q_exports = ['vote']


def _q_index(request):
    """recommendations timeline"""
    start = request.get_form_var('start')
    start = start and start.isdigit() and int(start) or 0
    limit = 20
    recs = Recommendation.gets(start=start, limit=limit)
    return st('recommendations.html', **locals())


def vote(request):
    user = request.user
    if user:
        rec_id = request.get_form_var('rec_id')
        r = Recommendation.get(rec_id)
        if r:
            r.add_vote(user.name)
            return json.dumps({'r': 1})
    return json.dumps({'r': 0})
