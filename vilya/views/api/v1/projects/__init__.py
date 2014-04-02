# -*- coding: utf-8 -*-

from __future__ import absolute_import
from quixote.errors import TraversalError
from vilya.models.user import User
from vilya.models.project import Project
from vilya.views.api import errors
from vilya.views.api.utils import RestAPIUI
from vilya.views.api.v1.projects.commits import CommitsUI
from vilya.views.api.v1.projects.files import FilesUI, FileUI
from vilya.views.api.v1.projects.contents import ContentsUI
from vilya.views.api.v1.projects.readme import ReadmeUI
from vilya.views.api.v1.projects.compare import CompareUI
from vilya.views.api.v1.projects.forks import ForksUI
from vilya.views.api.v1.projects.pulls import PullsUI


class ProjectsUI(RestAPIUI):
    _q_exports = []
    _q_methods = ['get', 'post']

    def get(self, request):
        projects = Project.gets()
        projects = [p.to_dict() for p in projects]
        return projects

    def post(self, request):
        user = request.user
        name = request.data.get('name', '')
        description = request.data.get('description', '')
        if user:
            p = Project.create(name=name,
                               owner_id=user.id,
                               creator_id=user.id,
                               description=description)
        return p.to_dict() if p else []

    def _q_lookup(self, request, name):
        user = User.get(name=name)
        if user:
            return UserUI(user)
        raise TraversalError


class ProjectUI(RestAPIUI):
    _q_exports = ['commits', 'files', 'contents', 'readme', 'file',
                  'compare', 'forks', 'pulls']
    _q_methods = ['get']

    def __init__(self, project):
        self.project = project

    def _q_lookup(self, request, part):
        raise TraversalError

    def get(self, request):
        project = self.project.to_dict()
        #project['links'] = {'commits': 'commits'}
        return project

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

    @property
    def forks(self):
        return ForksUI(self.project)

    @property
    def pulls(self):
        return PullsUI(self.project)


class UserUI(RestAPIUI):
    _q_exports = []
    _q_methods = []

    def __init__(self, user):
        self.user = user

    def _q_lookup(self, request, name):
        project = Project.get(name=name, owner_id=self.user.id)
        if project:
            return ProjectUI(project)
        raise errors.NotFoundError('project %s' % name)


class OrganizationUI(RestAPIUI):
    _q_exports = []
    _q_methods = []

    def __init__(self, organizaton):
        self.organizaton = organizaton

    def _q_lookup(self, request, name):
        project = Project.get(name=name, owner_id=self.organizaton.id)
        if project:
            return ProjectUI(project)
        raise errors.NotFoundError('project %s' % name)
