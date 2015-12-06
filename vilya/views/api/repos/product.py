# -*- coding: utf-8 -*-

from vilya.libs import api_errors
from vilya.views.api.utils import RestAPIUI


class ProductUI(RestAPIUI):
    _q_exports = []
    _q_methods = ['get', 'post']

    def __init__(self, repo):
        self.repo = repo

    def get(self, request):
        return {'content': self.repo.product}

    def post(self, request):
        content = request.data.get("content")
        if content is None:
            raise api_errors.MissingFieldError('content')
        self.repo.update_product(content)
        return {'content': self.repo.product}
