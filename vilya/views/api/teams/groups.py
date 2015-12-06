# -*- coding: utf-8 -*-
from vilya.libs import api_errors
from vilya.models.team_group import TeamGroup
from vilya.models.project import CodeDoubanProject
from vilya.views.api.utils import RestAPIUI


class GroupsUI(RestAPIUI):
    _q_exports = []
    _q_methods = ['get', 'post']

    def __init__(self, team):
        self.team = team

    def get(self, request):
        team = self.team
        rs = team.groups
        return [r.to_dict() for r in rs]

    def post(self, request):
        team = self.team
        user = request.user
        name = request.data.get('name')
        g = team.create_group(name=name)
        return g.to_dict() if g else {}

    def _q_lookup(self, request, part):
        team = self.team
        group = TeamGroup.get(team_id=team.id, name=part)
        if not group:
            raise api_errors.NotFoundError
        return GroupUI(group)


class GroupUI(RestAPIUI):
    _q_exports = ['members', 'projects', 'settings']
    _q_methods = ['get', 'post']

    def __init__(self, group):
        self.group = group

    def get(self, request):
        return self.group.to_dict()

    def post(self, request):
        return {}

    @property
    def members(self):
        return MembersUI(self.group)

    @property
    def projects(self):
        return ProjectsUI(self.group)


class MembersUI(RestAPIUI):
    _q_exports = []
    _q_methods = ['get', 'post']

    def __init__(self, group):
        self.group = group

    def get(self, request):
        rs = self.group.members
        return [r.as_dict() for r in rs]

    def post(self, request):
        user = request.user
        name = request.data.get('name')
        group = self.group
        team = group.team
        if not team.is_member(name):
            raise api_errors.NotAcceptableError
        u = group.add_user(user_id=name)
        if not u:
            raise api_errors.NotAcceptableError
        return u.user.as_dict()


class ProjectsUI(RestAPIUI):
    _q_exports = []
    _q_methods = ['get', 'post']

    def __init__(self, group):
        self.group = group

    def get(self, request):
        rs = self.group.projects
        return [r.as_dict() for r in rs]

    def post(self, request):
        user = request.user
        name = request.data.get('name')
        group = self.group
        team = group.team
        project = CodeDoubanProject.get_by_name(name)
        if not project:
            raise api_errors.NotAcceptableError
        if not team.is_project(project.id):
            raise api_errors.NotAcceptableError
        u = group.add_project(project_id=project.id)
        if not u:
            raise api_errors.NotAcceptableError
        return u.project.as_dict()
