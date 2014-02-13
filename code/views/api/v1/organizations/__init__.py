# -*- coding: utf-8 -*-

from __future__ import absolute_import
from quixote.errors import TraversalError, AccessError
from code.models.project import Project
from code.views.api import errors
from code.views.api.utils import RestAPIUI
from code.views.api.v1.projects import ProjectUI

_q_exports = []


def __call__(request):
    return _q_index(request)


def _q_index(request):
    return 'organizatons'


class OrganizationUI(RestAPIUI):
    _q_exports = []
    _q_methods = []

    def __init__(self, organizaton):
        self.organizaton = organizaton

    def _q_lookup(self, request, name):
        project = Project.get_by_name(name)
        if project:
            return ProjectUI(project)
        raise errors.NotFoundError('project %s', name)

