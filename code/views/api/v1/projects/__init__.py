# -*- coding: utf-8 -*-

from __future__ import absolute_import
from quixote.errors import TraversalError, AccessError
from code.models.user import User
from code.models.organization import Organization
from code.models.project import Project
from code.views.api.utils import RestAPIUI
from code.views.api.v1.projects.commits import CommitsUI
from code.views.api.v1.projects.files import FilesUI
from code.views.api.v1.projects.contents import ContentsUI


class ProjectsUI(RestAPIUI):
    _q_exports = []
    _q_methods = ['get']

    def _q_lookup(self, request, name):
        from code.views.api.v1.users import UserUI
        from code.views.api.v1.organizations import OrganizationUI

        user = User.get_by_name(name)
        if user:
            return UserUI(user)

        org = Organization.get_by_name(name)
        if org:
            return OrganizationUI(org)

        raise TraversalError

    def get(self, request):
        projects = Project.gets_by()
        projects=[p.as_dict() for p in projects]
        for p in projects:
            p['links'] = dict(commits='commits')
        return dict(projects=projects)


class ProjectUI(RestAPIUI):
    _q_exports = ['commits', 'files', 'contents']
    _q_methods = ['get']

    def __init__(self, project):
        self.project = project

    def _q_lookup(self, request, part):
        raise TraversalError

    def get(self, request):
        project = self.project.as_dict()
        project['links'] = {'commits':'commits'}
        return dict(project=project)

    @property
    def commits(self):
        return CommitsUI(self.project)

    @property
    def files(self):
        return FilesUI(self.project)

    @property
    def contents(self):
        return ContentsUI(self.project)

