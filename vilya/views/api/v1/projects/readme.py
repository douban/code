# -*- coding: utf-8 -*-

from __future__ import absolute_import
from vilya.views.api import errors
from vilya.views.api.utils import RestAPIUI


class ReadmeUI(RestAPIUI):
    _q_exports = []
    _q_methods = ['get']

    def __init__(self, project):
        self.project = project

    def get(self, request):
        path = request.get_form_var("path", "/")
        ref = request.get_form_var("ref", "HEAD")
        return dict(html=self.project.repo.get_readme(ref=ref,
                                                      path=path))
