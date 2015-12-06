# -*- coding: utf-8 -*-

from __future__ import absolute_import
import json

from vilya.models.project import CodeDoubanProject
from vilya.views.util import require_login_json, error_message

_q_exports = []


def _q_index(request):
    """get all watches"""
    user = request.user
    if user:
        return json.dumps([
            {'pid': str(p.id)}
            for p in CodeDoubanProject.get_watched_projects_by_user(user.name)])  # noqa
    return ''


def _q_lookup(request, proj_id):
    if request.method == "POST":
        return new(request, proj_id)
    elif request.method == "DELETE":
        return remove(request, proj_id)
    elif request.method == "GET":
        return has_watched(request, proj_id)
    else:
        return error_message("bad request")


@require_login_json
def new(request, proj_id):
    user = request.user
    CodeDoubanProject.add_watch(proj_id, user.name)
    return json.dumps({"ok": 1})


@require_login_json
def remove(request, proj_id):
    user = request.user
    CodeDoubanProject.del_watch(proj_id, user.name)
    return json.dumps({"ok": 1})


# FIXME: ugly fix
def has_watched(request, proj_id):
    user = request.user
    if CodeDoubanProject.has_watched(proj_id, user.name):
        return json.dumps({"ok": 1})
    return json.dumps({"ok": 0})
