# -*- coding: utf-8 -*-
from __future__ import absolute_import
from vilya.libs.template import st
from vilya.models.center.activity import Activity
from vilya.views.hub.center.activity import ActivitiesUI

_q_exports = ['new', 'activities']

activities = ActivitiesUI()


def _q_index(request):
    context = {}
    context['request'] = request
    if request.method == 'POST':
        user = request.user
        if not user:
            return request.redirect('/hub/center')
        title = request.get_form_var('title', '')
        description = request.get_form_var('body', '')
        type = request.get_form_var('type', 0)
        if not title:
            return request.redirect('/hub/center')
        Activity.create(title=title,
                        description=description,
                        type=int(type),
                        creator_id=user.name)
        return request.redirect('/hub/center')
    context['activities'] = Activity.gets(limit=30)
    return st('center/center.html', **context)


def new(request):
    context = {}
    context['request'] = request
    return st('center/new_activity.html', **context)
