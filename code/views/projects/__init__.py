# -*- coding: utf-8 -*-

from __future__ import absolute_import
from quixote.errors import TraversalError, AccessError
from code.libs.template import st
from code.models.project import Project
from code.models.user import User

_q_exports = ['new']


def __call__(request):
    return _q_index(request)


def _q_index(request):
    tdt = dict()
    session = request.session
    current_user = User.get_by(session.user) if session else None
    if current_user and request.method == "POST":
        name = request.get_form_var('name')
        description = request.get_form_var('description')
        p = Project.add(name=name,
                        description=description,
                        owner_id=current_user.id,
                        creator_id=current_user.id)
        if p:
            return request.redirect('projects/%s' % p.name)
        tdt['project'] = p
        return st('projects/index.html', **tdt)
    projects = Project.gets_by()
    tdt['projects'] = projects
    tdt['current_user'] = User.get_by(id=session.user) if session else None
    return st('projects/index.html', **tdt)


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
        tdt = dict()
        session = request.session
        tdt['project'] = self.project
        tdt['current_user'] = User.get_by(id=session.user) if session else None
        return st('/projects/repo.html', **tdt)

    def _q_lookup(self, request, part):
        raise TraversalError

