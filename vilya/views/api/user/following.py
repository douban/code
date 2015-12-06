# -*- coding: utf-8 -*-

from vilya.libs import api_errors
from vilya.views.api.utils import (
    RestAPIUI, http_status, api_list_user, jsonize)

_q_exports = []


@jsonize
def _q_index(request):
    if not request.user:
        return []
    following = request.user.get_following()
    return api_list_user(following)


def _q_lookup(request, username):
    return FollowUI(username)


class FollowUI(RestAPIUI):
    _q_exports = []
    _q_methods = ['get', 'put', 'delete']

    def __init__(self, username):
        if not username:
            raise api_errors.NotFoundError
        self.username = username

    def get(self, request):
        if self.user.is_following(self.username):
            request.response.set_status(204)
        else:
            request.response.set_status(404)

    @http_status(204)
    def put(self, request):
        self.user.follow(self.username)
        request.response.set_status(204)

    @http_status(204)
    def delete(self, request):
        self.user.unfollow(self.username)
