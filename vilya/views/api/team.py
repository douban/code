# -*- coding: utf-8 -*-

from vilya.libs import api_errors
from vilya.models.team import Team
from vilya.views.api.utils import jsonize
from vilya.views.api.teams.doc_project import DocProjectUI
from vilya.views.api.teams.groups import GroupsUI

_q_exports = []


def _q_lookup(request, name):
    return TeamUI(name)


class TeamUI(object):
    _q_exports = ['projects', 'members', 'doc_project', 'groups']

    def __init__(self, name):
        self.team = Team.get_by_uid(name)

    def __call__(self, request):
        return self._index(request)

    @jsonize
    def _index(self, request):
        if not self.team:
            raise api_errors.NotFoundError('team')
        return self.team.as_dict()

    def _q_access(self, request):
        request.response.set_content_type('application/json; charset=utf-8')

    @jsonize
    def projects(self, request):
        d = []
        projects = self.team.projects
        for project in projects:
            d.append(project.as_dict())
        return d

    @jsonize
    def members(self, request):
        d = []
        members = self.team.users
        for member in members:
            d.append(member.as_dict())
        return d

    @property
    def groups(self):
        return GroupsUI(self.team)

    @property
    def doc_project(self):
        return DocProjectUI(self.team)
