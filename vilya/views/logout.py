# -*- coding: utf-8 -*-

from __future__ import absolute_import
from quixote.errors import TraversalError, AccessError
from vilya.libs.template import st

_q_exports = []


def __call__(request):
    return _q_index(request)


def _q_index(request):
    user = request.user
    if request.method == 'POST':
        if user:
            user.clear_session()
        return request.redirect('/')
    context = {}
    context['current_user'] = user
    return st('logout.html', **context)
