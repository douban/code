# -*- coding: utf-8 -*-

from __future__ import absolute_import
from quixote.errors import TraversalError, AccessError
from code.libs.template import st
from code.models.project import Project
from code.models.user import User
from code.views.projects import ProjectUI

_q_exports = ['new']


def __call__(request):
    return _q_index(request)


def _q_index(request):
    tdt = dict()
    if request.method == "POST":
        name = request.get_form_var('name')
        password = request.get_form_var('password')
        email = request.get_form_var('email')
        description = request.get_form_var('description')
        user = User.add(name=name,
                        password=password,
                        description=description,
                        email=email)
        if user:
            tdt['user'] = user
            session = request.session
            session.set_user(user.id)
            return request.redirect('/')
    users = User.gets_by()
    tdt['users'] = users
    return st('users/index.html', **tdt)


def _q_lookup(request, part):
    raise TraversalError


class UserUI(object):
    _q_exports = []

    def __init__(self, user):
        self.user = user

    def __call__(self, request):
        pass

    def _q_index(self, request):
        pass

    def _q_lookup(self, request, part):
        project = Project.get_by_name(part)
        if project:
            return ProjectUI(project)
        raise TraversalError

