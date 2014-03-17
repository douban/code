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
        rs = self.project.fork_projects
        return [p.as_dict() for p in rs]

    def post(self, request):
        user = request.user
        project = self.project
        if project.owner_id == user.id:
            return {}
        p = project.add_fork(user.id)
        return p.as_dict() if p else {}
