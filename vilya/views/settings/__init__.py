# -*- coding: utf-8 -*-

from __future__ import absolute_import

from vilya.libs.auth.decorators import login_required
from vilya.models.user import User

_q_exports = ['emails', 'github', 'notification', 'ssh', 'codereview']


@login_required
def _q_index(request):
    return request.redirect("/settings/emails")


def _q_access(request):
    user = request.user
    if not user:
        return request.redirect(User.create_login_url(request.url))
