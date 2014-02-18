# -*- coding: utf-8 -*-

from __future__ import absolute_import
from quixote.errors import TraversalError, AccessError
from code.libs.template import st
from code.models.user import User

_q_exports = []


def __call__(request):
    return _q_index(request)


def _q_index(request):
    context = {}
    context['users'] = User.gets_by()
    context['current_user'] = request.user
    return st('projects/new.html', **context)
