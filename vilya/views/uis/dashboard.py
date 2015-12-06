# -*- coding: utf-8 -*-

from __future__ import absolute_import

from vilya.libs.template import st

from vilya.models.project import CodeDoubanProject


class DashboardUI(object):

    _q_exports = []

    def __init__(self, proj_name):
        self.proj_name = proj_name
        self.project = CodeDoubanProject.get_by_name(proj_name)

    def _q_index(self, request):
        return self._index(request)

    def _index(self, request):
        user = request.user
        project = self.project
        return st('/dashboard.html', **locals())
