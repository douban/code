# -*- coding: utf-8 -*-

from vilya.libs import api_errors
from vilya.models.project_issue import ProjectIssue
from vilya.views.api.utils import RestAPIUI


class IssuesUI(RestAPIUI):
    _q_exports = []
    _q_methods = ['get', 'post']

    def __init__(self, repo):
        self.repo = repo

    def get(self, request):
        return {}

    def post(self, request):
        return {}

    def _q_lookup(self, request, issue_number):
        repo = self.repo
        issue = ProjectIssue.get(project_id=repo.id,
                                 number=issue_number)
        if not issue:
            raise api_errors.NotFoundError('project issue')
        return IssueUI(request, repo, issue)


class IssueUI(RestAPIUI):
    _q_exports = ['milestone']
    _q_methods = ['get']

    def __init__(self, repo, issue):
        self.repo = repo
        self.issue = issue

    def get(self, request):
        return self.issue.as_dict()

    @property
    def milestone(self):
        return MilestoneUI(self.issue)


class MilestoneUI(RestAPIUI):
    _q_exports = []
    _q_methods = ['get', 'post', 'delete']

    def __init__(self, issue):
        self.issue = issue

    def get(self, request):
        return {}

    def post(self, request):
        return {}

    def delete(self, request):
        return {}
