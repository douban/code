# -*- coding: utf-8 -*-

from vilya.libs import api_errors
from vilya.views.api.utils import RestAPIUI


class DefaultBranchUI(RestAPIUI):
    _q_exports = []
    _q_methods = ['get', 'post']

    def __init__(self, repo):
        self.repo = repo

    def get(self, request):
        repo = self.repo.repo
        return {'content': repo.default_branch}

    def post(self, request):
        content = request.data.get("content")
        if content is None:
            raise api_errors.MissingFieldError('content')
        repo = self.repo.repo
        repo.update_default_branch(content)
        return {'content': repo.default_branch}
