# -*- coding: utf-8 -*-

from __future__ import absolute_import
from quixote.errors import TraversalError, AccessError
from vilya.views.api.v1.projects import ProjectsUI
from vilya.views.api.v1.users import UsersUI
from vilya.views.api.v1.post_receive import PostReceiveUI
from vilya.views.api.utils import APIRootBase


class APIRoot(APIRootBase):
    """API Root handler for version 1.x"""
    _q_exports = ['projects', 'post_receive', 'users']

    @property
    def version(self):
        return (1, 0)

    @property
    def projects(self):
        return ProjectsUI()

    @property
    def users(self):
        return UsersUI()

    @property
    def post_receive(self):
        return PostReceiveUI()
