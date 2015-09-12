# -*- coding: utf-8 -*-

from quixote.errors import TraversalError
from vilya.models.project import CodeDoubanProject
from vilya.models.page import Page


class PagesUI(object):
    _q_exports = []

    def __init__(self, project_name):
        self.project_name = project_name
        self.project = CodeDoubanProject.get_by_name(self.project_name)
        if not self.project:
            raise TraversalError()
        self.parts = []

    def _q_lookup(self, request, part):
        self.parts.append(part)
        return self

    def __call__(self, request):
        page = Page(self.project, "/".join(self.parts))
        if not page.exist:
            raise TraversalError
        request.response.set_content_type(page.content_type)
        return page.content

    def _q_index(self, request):
        page = Page(self.project, "/".join(self.parts))
        if not page.exist:
            raise TraversalError
        request.response.set_content_type(page.content_type)
        return page.content
