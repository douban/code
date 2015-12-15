# -*- coding: utf-8 -*-

from vilya.libs.template import st


_q_exports = []


def _q_index(request):
    user = request.user
    if user:
        watched_projects = user.watched_projects
        return st('/watching.html', **locals())
    return request.redirect("/hub/teams")
