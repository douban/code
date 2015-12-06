# -*- coding: utf-8 -*-
from quixote.errors import TraversalError
from vilya.libs.template import st
from vilya.models.center.activity import Activity


class ActivitiesUI(object):
    _q_exports = []

    def _q_index(self, request):
        context = {}
        context['request'] = request

        type = request.get_form_var('type', None)
        page = request.get_form_var('page', 1)
        if type:
            activities = Activity.gets(type=int(type),
                                       limit=10,
                                       start=int(page))
            total = Activity.count(type=int(type))
        else:
            activities = Activity.gets(limit=10, start=int(page))
            total = Activity.count()

        n_pages = (total - 1) / 10 + 1
        context['type'] = type
        context['page'] = page
        context['n_pages'] = n_pages

        context['activities'] = activities
        return st('center/activities.html', **context)

    def _q_lookup(self, request, part):
        id = int(part)
        a = Activity.get(id=id)
        if not a:
            raise TraversalError
        return ActivityUI(a)


class ActivityUI(object):
    _q_exports = []

    def __init__(self, activity):
        self.activity = activity

    def _q_index(self, request):
        context = {}
        context['request'] = request
        context['activity'] = self.activity
        return st('center/activity.html', **context)
