# -*- coding: utf-8 -*-

from vilya.libs import api_errors
from vilya.models.project import CodeDoubanProject
from vilya.views.api.utils import RestAPIUI, api_require_login


class CommittersUI(RestAPIUI):
    _q_exports = []
    _q_methods = ['get', 'post', 'delete']

    def __init__(self, repo):
        self.repo = repo

    def get(self, request):
        return [user.as_dict() for user in self.repo.committers]

    @api_require_login
    def post(self, request):
        content = request.data.get("content")
        if content is None:
            raise api_errors.MissingFieldError('content')
        CodeDoubanProject.add_committer(self.repo.id, content)
        return {}

    @api_require_login
    def delete(self, request):
        content = request.data.get("content")
        if content is None:
            raise api_errors.MissingFieldError('content')
        CodeDoubanProject.del_committer(self.repo.id, content)
        return {}
