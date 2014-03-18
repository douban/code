# -*- coding: utf-8 -*-

from __future__ import absolute_import
from vilya.views.api.errors import NotFoundError
from vilya.views.api.utils import RestAPIUI


class ForksUI(RestAPIUI):
    _q_exports = []
    _q_methods = ['get', 'post']

    def __init__(self, project):
        self.project = project

    def get(self, request):
        rs = self.project.forks
        return [p.to_dict() for p in rs]

    def post(self, request):
        user = request.user
        project = self.project
        if project.owner_id == user.id:
            return {}
        p = project.fork(user.id)
        return p.to_dict() if p else {}
