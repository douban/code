# -*- coding: utf-8 -*-

from __future__ import absolute_import
from quixote.errors import TraversalError, AccessError
from vilya.libs.template import st
from vilya.models.project import Project
from vilya.models.user import User
from vilya.views.projects import ProjectUI
from vilya.libs.text import _validate_email

_q_exports = ['new']


def __call__(request):
    return _q_index(request)


def _q_index(request):
    context = {}
    if request.method == "POST":
        name = request.get_form_var('name')
        password = request.get_form_var('password')
        email = request.get_form_var('email')
        description = request.get_form_var('description')

        # Forced mail format must be correct
        if not _validate_email(email):
            context['name'] = name
            context['not_validate_email'] = True
            context['password'] = password
            context['email'] = email
            context['description'] = description
            return st('users/new.html', **context)

        user = User.create(name=name,
                        password=password,
                        description=description,
                        email=email)
        if user:
            context['user'] = user
            user.set_session(request)
            request.user = user
            return request.redirect('/')
    users = User.gets_by()
    context['users'] = users
    return st('users/index.html', **context)


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
        project = Project.get(owner_id=self.user.id, name=part)
        if project:
            return ProjectUI(project)
        raise TraversalError
