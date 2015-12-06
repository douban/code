# -*- coding: utf-8 -*-

from vilya.libs import api_errors
from vilya.models.project import CodeDoubanProject
from vilya.models.team_project import TeamProject
from vilya.views.api.utils import RestAPIUI


class DocProjectUI(RestAPIUI):
    _q_exports = []
    _q_methods = ['get', 'post']

    def __init__(self, team):
        self.team = team

    def get(self, request):
        project = self.team.doc_project
        return {'content': project and project.name}

    def post(self, request):
        content = request.data.get("content")
        if content is None:
            raise api_errors.MissingFieldError('content')
        doc_project = self.team.doc_project
        project = CodeDoubanProject.get(content)
        if not project:
            return {'content': doc_project and doc_project.name}
        team_projects = TeamProject.gets_by(team_id=self.team.id)
        team_project = team_projects[0] if team_projects else None
        if team_project:
            team_project.project_id = project.id
            team_project.save()
        else:
            TeamProject.create(team_id=self.team.id, project_id=project.id)
        return {'content': project.name}
