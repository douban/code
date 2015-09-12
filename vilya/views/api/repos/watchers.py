# -*- coding: utf-8 -*-

from vilya.views.api.utils import RestAPIUI


class WatchersUI(RestAPIUI):
    _q_exports = []
    _q_methods = ['get']

    def __init__(self, repo):
        self.repo = repo

    def get(self, request):
        watchers = self.repo.get_watch_users()
        return [u.as_dict() for u in watchers]
