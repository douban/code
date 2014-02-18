# -*- coding: utf-8 -*-

from __future__ import absolute_import
from vilya.views.api.utils import RestAPIUI


class FilesUI(RestAPIUI):
    _q_exports = []
    _q_methods = ['get']

    def __init__(self, project):
        self.project = project

    def get(self, request):
        path = request.get_form_var('path', '')
        rev = request.get_form_var('rev', 'HEAD')
        repo = self.project.repo
        files = repo.get_tree(rev, path=path)
        return [f for f in files]
