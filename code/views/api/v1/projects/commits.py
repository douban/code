# -*- coding: utf-8 -*-

from __future__ import absolute_import
from code.views.api.utils import RestAPIUI


class CommitsUI(RestAPIUI):
    _q_exports = []
    _q_methods = ['get']

    def __init__(self, project):
        self.project = project

    def get(self, request):
        repo = self.project.repo
        commits = repo.get_commits('HEAD', 'HEAD~5')
        if not commits:
            return {'commits':[]}
        return dict(commits=[commit.as_dict() for commit in commits])

