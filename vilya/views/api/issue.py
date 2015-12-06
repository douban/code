# -*- coding: utf-8 -*-
import warnings

from vilya.libs import api_errors
from vilya.models.project import CodeDoubanProject
from vilya.models.issue import Issue
from vilya.models.project_issue import ProjectIssue
from vilya.views.api.utils import RestAPIUI
from vilya.views.api.comments import IssueCommentsUI


class ProjectIssueUI(RestAPIUI):
    _q_exports = ['comments']
    _q_methods = ['get', 'patch']

    def __init__(self, request, proj_name, issue_number):
        self.proj_name = proj_name
        self.issue_number = issue_number
        self.project = CodeDoubanProject.get_by_name(self.proj_name)
        self.project_issue = ProjectIssue.get(project_id=self.project.id,
                                              number=self.issue_number)
        if not self.project_issue:
            raise api_errors.NotFoundError('project issue')
        self.comments = IssueCommentsUI(request, self.project_issue)
        self.user = request.user

    def get(self, request):
        return self.project_issue.as_dict()

    def patch(self, request):
        issue = Issue.get_cached_issue(self.project_issue.issue_id)
        if self.user.username != issue.creator_id:
            raise api_errors.NotTheAuthorError('project issue', 'edit')
        data = request.data
        state = data.get("state")
        if state in ("open", "closed") and state != issue.state:
            if state == "open":
                issue.open(self.user.username)
            else:
                issue.close(self.user.username)

        title = data.get("title")
        title = title if title else issue.title
        description = data.get("description")
        description = description if description else issue.description
        issue.update(title, description)
        new_issue = ProjectIssue.get(project_id=self.project.id,
                                     number=self.issue_number)
        return new_issue.as_dict()


class IssuesUI(RestAPIUI):
    _q_exports = []
    _q_methods = ['get', 'post']

    def __init__(self, request, proj_name):
        self.proj_name = proj_name
        self.project = CodeDoubanProject.get_by_name(proj_name)

    def get(self, request):
        page = int(request.get_form_var('page', 1))
        count = int(request.get_form_var('count', 25))
        start = (page - 1) * count
        state = request.get_form_var('state', None)
        project = self.project
        project_issues = ProjectIssue.gets_by_target(project.id, state=state,
                                                     start=start, limit=count)
        return [issue.as_dict() for issue in project_issues]

    def post(self, request):
        title = request.data.get("title")
        if not title:
            raise api_errors.MissingFieldError('title')

        # optional parameters
        description = request.data.get("description", "")
        assignee = request.data.get("assignee", "")
        tags = request.data.get("tags", [])
        participants = request.data.get("participants", [])

        if not isinstance(tags, list):
            raise api_errors.InvalidFieldError('tags', "an array of strings")

        issue = ProjectIssue.add(title=title,
                                 description=description,
                                 creator=request.user.username,
                                 project=self.project.id,
                                 assignee=assignee)
        issue.add_tags(tags, issue.project_id)
        issue.add_participants(participants)

        return issue.as_dict()

    def _q_lookup(self, request, issue_number):
        return ProjectIssueUI(request, self.proj_name, issue_number)


# deprecated
# 此处已弃用，请使用 api/project_name/issues/issue_number 来获取单个issue
class IssueUI:
    _q_exports = []

    def __init__(self, request, proj_name):
        self.proj_name = proj_name

    def _q_lookup(self, request, issue_number):
        warnings.warn('IssueUI is deprecated', DeprecationWarning)
        return ProjectIssueUI(request, self.proj_name, issue_number)
