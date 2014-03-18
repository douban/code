# -*- coding: utf-8 -*-

from __future__ import absolute_import
from quixote.errors import TraversalError, AccessError
from vilya.libs.template import st
from vilya.views.util import jsonize
from vilya.views.static import StaticUI
from vilya.views.organizations import OrganizationUI
from vilya.views.users import UserUI
from vilya.models.user import User
from vilya.models.organization import Organization

_q_exports = ['api',
              'organizations',
              'users',
              'projects',
              'login',
              'logout',
              'vilya']


def _q_exception_handler(request, exception):
    if isinstance(exception, TraversalError):
        error = exception.title
        current_user = request.user
        return st('/errors/404.html', **locals())
    if isinstance(exception, AccessError):
        error = exception.title
        return st('/errors/401.html', **locals())
    else:
        raise exception


def vilya(request):
    context = {}
    context['current_user'] = request.user
    return st("vilya/app.html", **context)


def _q_index(request):
    context = {}
    context['current_user'] = request.user
    return st("index.html", **context)


def __call__(request):
    return _q_index(request)


def _q_lookup(request, name):
    if name in ['static', 'js', 'css']:
        return StaticUI(request, name)

    user = User.get(name=name)
    if user:
        return UserUI(user)

    org = Organization.get(name=name)
    if org:
        return OrganizationUI(org)

    raise TraversalError


class HubUI(object):
    _q_exports = []

    def __init__(self, name):
        pass

    def __call__(self, request):
        pass

    def _q_index(self, request):
        pass

    def _q_lookup(self, request, part):
        pass
