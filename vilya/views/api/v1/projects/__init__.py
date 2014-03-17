# -*- coding: utf-8 -*-

from __future__ import absolute_import
from quixote.errors import TraversalError
from vilya.models.user import User
from vilya.models.organization import Organization
from vilya.models.project import Project
from vilya.views.api.utils import RestAPIUI
from vilya.views.api.v1.projects.commits import CommitsUI
from vilya.views.api.v1.projects.files import FilesUI, FileUI
from vilya.views.api.v1.projects.contents import ContentsUI
from vilya.views.api.v1.projects.readme import ReadmeUI
from vilya.views.api.v1.projects.compare import CompareUI


class ProjectsUI(RestAPIUI):
    _q_exports = []
    _q_methods = ['get']

    def _q_lookup(self, request, name):
        from vilya.views.api.v1.users import UserUI
        from vilya.views.api.v1.organizations import OrganizationUI

        user = User.get_by_name(name)
        if user:
            return UserUI(user)

        org = Organization.get_by_name(name)
        if org:
            return OrganizationUI(org)

        raise TraversalError

    def get(self, request):
        projects = Project.gets_by()
        projects = [p.as_dict() for p in projects]
        return projects


class ProjectUI(RestAPIUI):
    _q_exports = ['commits', 'files', 'contents', 'readme', 'file',
                  'compare']
    _q_methods = ['get']

    def __init__(self, project):
        self.project = project

    def _q_lookup(self, request, part):
        raise TraversalError

    def get(self, request):
        project = self.project.as_dict()
        project['links'] = {'commits': 'commits'}
        return dict(project=project)

    @property
    def commits(self):
        return CommitsUI(self.project)

    @property
    def files(self):
        return FilesUI(self.project)

    @property
    def file(self):
        return FileUI(self.project)

    @property
    def contents(self):
        return ContentsUI(self.project)

    @property
    def readme(self):
        return ReadmeUI(self.project)

    @property
    def compare(self):
        return CompareUI(self.project)
