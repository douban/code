# -*- coding: utf-8 -*-
from __future__ import absolute_import
from quixote import get_session_manager

from vilya.libs.template import st

_q_exports = []


def __call__(request):
    return _q_index(request)


def _q_index(request):
    user = request.user
    if request.method == 'POST':
        if user:
            continue_url = request.get_form_var(
                'continue', '') or request.get_form_var('Referer', '')
            get_session_manager().expire_session(request)
        return request.redirect(continue_url or '/')
    context = {}
    context['current_user'] = user
    return st('logout.html', **context)
