# -*- coding: utf-8 -*-

from __future__ import absolute_import
from quixote.errors import TraversalError, AccessError
from code.libs.template import st
from code.models.user import User

_q_exports = []


def __call__(request):
    return _q_index(request)


def _q_index(request):
    session = request.session
    tdt = {}
    tdt['session'] = session
    tdt['current_user'] = User.get_by(id=session.user) if session else None
    if request.method == 'POST':
        session.set_user(None)
        return request.redirect('/')
    return st('logout.html', **tdt)
