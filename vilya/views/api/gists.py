# -*- coding: utf-8 -*-
import json

from vilya.libs import api_errors
from vilya.models.gist import (
    Gist, gist_detail, PRIVILEGE_PUBLIC, PRIVILEGE_SECRET)
from vilya.views.api.gist import GistUI
from vilya.views.api.utils import json_body

_q_exports = ['starred']


@json_body
def _q_index(request):
    if request.method == 'POST':
        desc = request.data.get('description') or request.get_form_var(
            'description', '')

        # DEPRECATED, will removed in future, use json to post data
        file_names = request.get_form_var('file_name', '')
        file_contents = request.get_form_var('file_contents', '')

        if not request.data.get('public'):
            is_public = PRIVILEGE_SECRET
        else:
            is_public = PRIVILEGE_PUBLIC

        files = request.data.get('files')
        if files:
            file_names = []
            file_contents = []
            for file_name, file in files.iteritems():
                file_names.append(file_name)
                file_contents.append(file.get("content"))

        if file_names and file_contents:
            user = request.user
            user_id = user and user.username or Gist.ANONYMOUS
            gist = Gist.add(desc, user_id, is_public,
                            file_names, file_contents)
            ret = gist_detail(gist, include_forks=True)
            request.response.set_status(201)
            return json.dumps(ret)
        else:
            raise api_errors.UnprocessableEntityError

    if request.user:
        gists = Gist.gets_by_owner(request.user.username, start=request.start)
    else:
        gists = Gist.discover('discover', start=request.start, limit=5)

    ret = [gist_detail(g) for g in gists]
    request.response.set_status(200)
    return json.dumps(ret)


def starred(request):
    user = request.user
    if user:
        gists = Gist.stars_by_user(user.username, start=request.start)
    else:
        ret = []
    ret = [gist_detail(g) for g in gists]
    request.response.set_status(200)
    return json.dumps(ret)


def _q_lookup(request, item):
    if item.isdigit():
        return GistUI(request, item)
    raise api_errors.NotFoundError("gist")


def _q_access(request):
    request.response.set_content_type('application/json; charset=utf-8')

    start = request.get_form_var('start', '0')
    request.start = start.isdigit() and int(start) or 0
