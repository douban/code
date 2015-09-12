# -*- coding: utf-8 -*-

from __future__ import absolute_import

from vilya.libs.template import st
from vilya.models.project import CodeDoubanProject


class WatchersUI(object):
    _q_exports = []

    template = 'watchers.html'

    def __init__(self, proj_name):
        self.proj_name = proj_name
        self.project = CodeDoubanProject.get_by_name(proj_name)

    def _q_index(self, request):
        project = self.project
        user = request.user
        users = self.get_users()
        projects = self.get_projects()
        return st(self.template, **locals())

    def get_users(self):
        return self.project.get_watch_users()

    def get_projects(self):
        return []


class ForkersUI(WatchersUI):
    template = 'forkers.html'

    def get_users(self):
        return self.project.get_forked_users()

    def get_projects(self):
        return self.project.get_forked_projects()
