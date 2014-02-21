# -*- coding: utf-8 -*-

from __future__ import absolute_import
from quixote.errors import TraversalError
from vilya.libs.template import st
from vilya.models.project import Project

_q_exports = ['new']


def __call__(request):
    return _q_index(request)


def _q_index(request):
    current_user = request.user
    if current_user and request.method == "POST":
        name = request.get_form_var('name')
        description = request.get_form_var('description')
        p = Project.add(name=name,
                        description=description,
                        owner_id=current_user.id,
                        creator_id=current_user.id)
        if p:
            return request.redirect('projects/%s' % p.name)
        has_proj = Project.get_by_name_and_owner(name, current_user.id)
        error = 'Create Failure. Please contact the administrator!'
        if has_proj is not None:
            error = 'Project has exists, Please confirm!'
        return st('/errors/common.html', **locals())

    projects = Project.gets_by()
    return st('projects/index.html', **locals())


def _q_lookup(request, part):
    p = Project.get_by_name(part)
    if p:
        return ProjectUI(p)
    raise TraversalError


class ProjectUI(object):
    _q_exports = []

    def __init__(self, project):
        self.project = project

    def __call__(self, request):
        return self._q_index(request)

    def _q_index(self, request):
        context = {}
        context['project'] = self.project
        context['current_user'] = request.user
        return st('/projects/repo.html', **context)

    def _q_lookup(self, request, part):
        raise TraversalError
