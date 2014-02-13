# -*- coding: utf-8 -*-

from __future__ import absolute_import
from quixote.errors import TraversalError, AccessError
from code.libs.template import st
from code.views.util import jsonize
from code.views.static import StaticUI
from code.views.organizations import OrganizationUI
from code.views.users import UserUI
from code.models.user import User
from code.models.organization import Organization

_q_exports = ['api',
              'organizations',
              'users',
              'projects',
              'login',
              'logout']


def _q_exception_handler(request, exception):
    if isinstance(exception, TraversalError):
        error = exception
        return st('/errors/404.html', **locals())
    if isinstance(exception, AccessError):
        error = exception
        return st('/errors/401.html', **locals())
    else:
        raise exception


def _q_index(request):
    tdt = {}
    session = request.session
    tdt['session'] = session
    tdt['current_user'] = User.get_by(id=session.user) if session else None
    return st("index.html", **tdt)


def __call__(request):
    return _q_index(request)


def _q_lookup(request, name):
    if name in ['static', 'js', 'css']:
        return StaticUI(request, name)

    user = User.get_by_name(name)
    if user:
        return UserUI(user)

    org = Organization.get_by_name(name)
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

