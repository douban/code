# -*- coding: utf-8 -*-

from __future__ import absolute_import
from quixote import get_session
from quixote.errors import TraversalError, AccessError
from code.libs.template import st
from code.models.user import User

_q_exports = []


def __call__(request):
    return _q_index(request)


def _q_index(request):
    if request.method == 'POST':
        name = request.get_form_var('login')
        password = request.get_form_var('password')
        user = User.get_by_name(name)
        if user and user.validate_password(password):
            session = request.session
            session.set_user(user.id)
            return request.redirect('/')
    return st('login.html')
