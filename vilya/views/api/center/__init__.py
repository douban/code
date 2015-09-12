# -*- coding: utf-8 -*-
from __future__ import absolute_import
from vilya.libs import api_errors
from vilya.views.api.utils import jsonize, RestAPIUI
from vilya.models.center.activity import Activity


class CenterUI(RestAPIUI):
    _q_exports = ['activity']
    _q_methods = ['post']

    def post(self, request):
        user = request.user
        title = request.get_form_var('title')
        desc = request.get_form_var('description', '')
        type = request.get_form_var('type')
        creator_id = user.name
        if not title:
            raise api_errors.MissingFieldError('title')
        if type is not None:
            type = int(type)
        else:
            type = 0
        a = Activity.create(title=title,
                            description=desc,
                            type=type,
                            creator_id=creator_id)
        return a.to_dict()

    @jsonize
    def activity(self, request):
        # TODO: optimize limit
        start = request.get_form_var('start', 0)
        limit = request.get_form_var('limit', 10)
        rs = Activity.gets(start=int(start), limit=int(limit))
        return [r.to_dict() for r in rs]
