#!/usr/bin/env python
# encoding: utf-8
from quixote.errors import TraversalError

from vilya.models.notification import Notification
from vilya.libs.auth.check_auth import check_auth
from vilya.libs import api_errors
from vilya.views.api.utils import jsonize, json_body, http_status

_q_exports = ['mark_all_as_read', 'mark_as_read']


def _q_access(request):
    check_auth(request)
    if not request.user:
        raise TraversalError()


@jsonize
def _q_index(request):
    start = request.get_form_var('start', '0')
    limit = request.get_form_var('count', '20')
    if start.isdigit() and limit.isdigit():
        start = int(start)
        limit = int(limit)
    else:
        start = 0
        limit = 20
    user = request.user
    notifications = Notification.get_data(user.name)
    return notifications[start:(start+limit)]


@jsonize
@json_body
@http_status(204)
def mark_as_read(request):
    if request.method == "POST":
        uid = request.data.get('uid')
        if uid:
            Notification.mark_as_read(request.user.name, uid)
            return {"status": 1}
        else:
            raise api_errors.MissingFieldError('uid')
    raise api_errors.MethodNotAllowedError()


@jsonize
@http_status(204)
def mark_all_as_read(request):
    if request.method == "POST":
        Notification.mark_all_as_read(request.user.name)
        return {"status": 1}
    else:
        raise api_errors.MethodNotAllowedError()
