# -*- coding: utf-8 -*-

from __future__ import absolute_import

from vilya.libs.template import st
from vilya.models.project import CodeDoubanProject

_q_exports = []


class SettingsConfUI:
    _q_exports = []

    def __init__(self, proj_name):
        self.proj_name = proj_name

    def _q_index(self, request):
        user = request.user
        tdt = {
            'user': user,
            'project': CodeDoubanProject.get_by_name(self.proj_name),
            'request': request,
        }
        return st('settings/config.html', **tdt)
