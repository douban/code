# -*- coding: utf-8 -*-

from vilya.libs import api_errors
from vilya.models.commit_status import ExtraCommitStatus
from vilya.views.api.utils import RestAPIUI, jsonize, json_body, http_status


class ExtraStatusUI(RestAPIUI):
    _q_exports = []
    _q_methods = ['get', 'post']

    def __init__(self, repo, commit):
        self.commit = commit
        self.repo = repo
        self.status = ExtraCommitStatus(repo, commit.sha)

    @jsonize
    @json_body
    @http_status(201)
    def _post(self, req):
        return self.post(req)

    def get(self, request):
        status = self.status
        return status.get_extra()

    def post(self, request):
        status = self.status
        data = request.data
        if not isinstance(data, dict):
            raise api_errors.UnprocessableEntityError
        return status.update_extra(**data)
