# -*- coding: utf-8 -*-

import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from vilya.libs.template import st


def watch_index(request):
    from vilya.models.project import CodeDoubanProject
    """get all watches"""
    user = request.user
    if user:
        return HttpResponse(json.dumps([
            {'pid': str(p.id)}
            for p in CodeDoubanProject.get_watched_projects_by_user(user.name)]))  # noqa
    return HttpResponse('')


@csrf_exempt
def watch(request, id):
    from vilya.models.project import CodeDoubanProject
    from vilya.views.util import error_message

    def new(request, proj_id):
        user = request.user
        CodeDoubanProject.add_watch(proj_id, user.name)
        return HttpResponse(json.dumps({"ok": 1}))


    def remove(request, proj_id):
        user = request.user
        CodeDoubanProject.del_watch(proj_id, user.name)
        return HttpResponse(json.dumps({"ok": 1}))


    # FIXME: ugly fix
    def has_watched(request, proj_id):
        user = request.user
        if CodeDoubanProject.has_watched(proj_id, user.name):
            return HttpResponse(json.dumps({"ok": 1}))
        return HttpResponse(json.dumps({"ok": 0}))

    proj_id = id
    if request.method == "POST":
        return new(request, proj_id)
    elif request.method == "DELETE":
        return remove(request, proj_id)
    elif request.method == "GET":
        return has_watched(request, proj_id)
    else:
        return HttpResponse(error_message("bad request"))


@csrf_exempt
def fetch(request, id):
    from vilya.views.util import error_message
    from tasks import fetch_mirror_project
    if request.method == "POST":
        fetch_mirror_project(id)
        return HttpResponse(json.dumps({"ok": 1}))
    return HttpResponse(error_message("bad request"))


def watchers(request, username, projectname):
    from vilya.models.project import CodeDoubanProject
    name = '/'.join([username, projectname])
    project = CodeDoubanProject.get_by_name(name)
    projects = []
    user = request.user
    users = project.get_watch_users()
    return HttpResponse(st('watchers.html', **locals()))


def forkers(request, username, projectname):
    from vilya.models.project import CodeDoubanProject
    name = '/'.join([username, projectname])
    project = CodeDoubanProject.get_by_name(name)
    projects = project.get_forked_projects()
    user = request.user
    users = project.get_forked_users()
    return HttpResponse(st('watchers.html', **locals()))
