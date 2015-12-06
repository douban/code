# -*- coding: utf-8 -*-

from __future__ import absolute_import

from quixote.errors import TraversalError
from vilya.libs.template import st
from vilya.models.project import CodeDoubanProject
from itertools import groupby
from vilya.models.comment import Comment


class CompareUI(object):

    _q_exports = []

    def __init__(self, proj_name):
        self.proj_name = proj_name
        project = CodeDoubanProject.get_by_name(proj_name)
        self.project = project

    def _q_index(self, request):
        return TraversalError(
            'please provide valid start & end revisions: /compare/start...end')

    def _q_lookup(self, request, revrange):
        current_user = request.user
        try:
            sha1, sha2 = revrange.split('...')
        except ValueError:
            raise TraversalError(
                'please provide valid start & end revisions: /compare/sha1...sha2')  # noqa
        project = self.project
        commits = project.repo.get_commits(sha2, sha1)
        if commits is False:
            raise TraversalError()
        lasttime = commits and commits[0].author_time.strftime(
            "%Y-%m-%d %H:%M:%S") or 'UNKNOWN'
        grouped_commits = groupby(commits, lambda c: c.author_time.date())
        n_commits = len(commits)
        n_authors = len(set(c.author.username for c in commits))
        diff = project.repo.get_diff(sha2,
                                     from_ref=sha1,
                                     rename_detection=True)
        #diffs = project.git.get_3dot_diff(sha1, sha2)
        n_files = diff.length if diff else 0
        comments = []
        for ci in commits:
            comments.extend(Comment.gets_by_proj_and_ref(project.id, ci.sha))
        branches = project.repo.branches
        tags = project.repo.tags
        ref = project.default_branch
        n_comments = len(comments)
        ref_type = 'branch' if ref in branches else 'tag' \
                   if ref in tags else 'tree'
        return st('compare.html', **locals())
