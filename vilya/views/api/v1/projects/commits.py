# -*- coding: utf-8 -*-

from __future__ import absolute_import
from vilya.views.api.utils import RestAPIUI

COMMITS_PER_PAGE = 35


class CommitsUI(RestAPIUI):
    _q_exports = []
    _q_methods = ['get']

    def __init__(self, project):
        self.project = project

    def get(self, request):
        repo = self.project.repo
        ref = request.get_form_var('ref', 'HEAD')
        author = request.get_form_var('author')
        page = int(request.get_form_var('page', 1))
        skip = COMMITS_PER_PAGE * (page - 1)
        commits = repo.get_commits(ref,
                                   skip=skip,
                                   max_count=COMMITS_PER_PAGE,
                                   author=author)
        if not commits:
            return []
        return [commit.as_dict() for commit in commits]
