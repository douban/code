# -*- coding: utf-8 -*-

from vilya.views.api.utils import RestAPIUI


class PushUI(RestAPIUI):
    _q_exports = []
    _q_methods = ['get', 'post', 'delete']

    def __init__(self, repo):
        self.repo = repo

    def get(self, request):
        return {'content': self.repo.can_push}

    def post(self, request):
        self.repo.update_can_push(True)
        return {'content': 1}

    def delete(self, request):
        self.repo.update_can_push(False)
        return {'content': 0}
