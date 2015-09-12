# -*- coding: utf-8 -*-
import json

from quixote.errors import TraversalError

from vilya.models.project import CodeDoubanProject
from vilya.models.team import Team
from vilya.views.api.utils import jsonize

_q_exports = []


def _q_index(request):
    sortby = request.get_form_var('sortby')
    if sortby in CodeDoubanProject.PROJECTS_SORT_BYS:
        project_list = CodeDoubanProject.get_projects(sortby=sortby)
    else:
        project_list = CodeDoubanProject.get_projects()

    team_uid = request.get_form_var('by_dept', '')
    team = Team.get_by_uid(team_uid)
    if team:
        project_ids = team.project_ids
        project_list = (CodeDoubanProject.gets(project_ids)
                        if project_ids else [])

    without_commits = request.get_form_var('without_commits') or False
    data = {}
    data['projects'] = [project.get_info(
        without_commits=without_commits) for project in project_list]
    return json.dumps(data)


def _q_lookup(request, name):
    return ProjectUI(request, name)


class ProjectUI:
    _q_exports = []

    def __init__(self, request, name):
        self.name = name
        self._project = CodeDoubanProject.get_by_name(name)

    def __call__(self, request):
        return self._index(request)

    def _q_index(self, request):
        return self._index(request)

    @jsonize
    def _index(self, request):
        if not self._project:
            raise TraversalError()
        dic = self._project.as_dict()
        dic['readme'] = self._project.readme
        return dic

    def _q_lookup(self, request, name):
        self.name = self.name + "/" + name
        project = CodeDoubanProject.get_by_name(self.name)
        if not project:
            raise TraversalError()
        return json.dumps(project.as_dict())
