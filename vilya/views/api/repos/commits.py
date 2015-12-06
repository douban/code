# -*- coding: utf-8 -*-

from vilya.libs import api_errors
from vilya.views.api.utils import RestAPIUI
from vilya.views.api.repos.extra_status import ExtraStatusUI


class CommitsUI(RestAPIUI):
    _q_exports = []
    _q_methods = ['get']

    def __init__(self, repo):
        if not repo:
            raise api_errors.NotFoundError("repo")
        self.repo = repo

    def get(self, request):
        _from = request.get_form_var('from') or 'HEAD~5'
        _to = request.get_form_var('to') or 'HEAD'
        first_parent = request.get_form_var('first_parent')
        first_parent = True if first_parent else None
        files = request.get_form_var('files')
        files = True if files else None
        repo = self.repo.repo
        if not repo:
            return []
        commits = repo.get_commits(_to,
                                   from_ref=_from,
                                   first_parent=first_parent)
        if not commits:
            return []
        return [commit.as_dict(with_files=files) for commit in commits]

    def _q_lookup(self, request, part):
        repo = self.repo.repo
        commit = repo.get_commit(part)
        if not commit:
            raise api_errors.NotFoundError('commit %s' % part)
        return CommitUI(self.repo, commit)


class CommitUI(RestAPIUI):
    _q_exports = ['extra_status']
    _q_methods = ['get']

    def __init__(self, repo, commit):
        self.repo = repo
        self.commit = commit

    def get(self, request):
        files = request.get_form_var('files')
        files = True if files else None
        return self.commit.as_dict(with_files=files)

    @property
    def extra_status(self):
        return ExtraStatusUI(self.repo, self.commit)
