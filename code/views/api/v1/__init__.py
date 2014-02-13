# -*- coding: utf-8 -*-

from __future__ import absolute_import
from quixote.errors import TraversalError, AccessError
from code.views.api.v1.projects import ProjectsUI
from code.views.api.v1.post_receive import PostReceiveUI
from code.views.api.utils import APIRootBase

class APIRoot(APIRootBase):
    """API Root handler for version 1.x"""
    _q_exports = ['projects', 'post_receive']

    @property
    def version(self):
        return (1, 0)

    @property
    def projects(self):
        return ProjectsUI()

    @property
    def post_receive(self):
        return PostReceiveUI()
