# -*- coding: utf-8 -*-

from vilya.libs import api_errors
from vilya.views.api.utils import RestAPIUI


class InternUI(RestAPIUI):
    _q_exports = []
    _q_methods = ['get', 'post', 'delete']

    def __init__(self, repo):
        self.repo = repo

    def get(self, request):
        return {'content': self.repo.intern_banned}

    def post(self, request):
        content = request.data.get("content")
        if content is None:
            raise api_errors.MissingFieldError('content')
        self.repo.update_intern_banned(content)
        return {'content': content}

    def delete(self, request):
        self.repo.update_intern_banned(None)
        return {'content': None}
