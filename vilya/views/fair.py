# -*- coding: utf-8 -*-

from vilya.libs.template import st

from vilya.models.fair import get_fair
from vilya.models.issue import Issue
from vilya.models.fair_issue import FairIssue
from vilya.models.tag import Tag, TAG_TYPE_FAIR_ISSUE

from vilya.views.hub.team import TeamIssueBoardUI, TeamIssueUI
from vilya.views.uis.issue import get_order_type

_q_exports = []


class FairUI(TeamIssueBoardUI):
    _q_exports = TeamIssueBoardUI._q_exports + ['issue_comments']
    cls = FairIssue

    def __init__(self, request, name=''):
        self.team = get_fair()
        self.name = name

    def _q_access(self, request):
        pass

    def _q_index(self, request):
        if self.name == 'issues':
            return request.redirect(self.team.url)

        user = request.user
        team = self.team
        page = request.get_form_var('page', 1)
        state = request.get_form_var('state', 'open')
        order = get_order_type(request, 'fair_issues_order')

        all_issues = []

        selected_tag_names = request.get_form_var('tags', '')
        if selected_tag_names:
            selected_tag_names = selected_tag_names.split(',')
            issue_ids = Tag.get_type_ids_by_names_and_target_id(
                TAG_TYPE_FAIR_ISSUE,
                selected_tag_names,
                team.id)
            all_issues = self.cls.gets_by_issue_ids(issue_ids, state)
        else:
            all_issues = self.cls.gets_by_target(team.id, state, order=order)

        n_team_issue = len(all_issues)
        show_tags = team.get_group_tags(selected_tag_names)
        is_closed_tab = None if state == 'open' else True
        n_pages = 1
        return st('/fair.html', **locals())

    def _q_lookup(self, request, name):
        if name.isdigit():
            return FairIssueUI(name)
        return FairUI(request, name)

    @property
    def issue_comments(self):
        from vilya.views.hub.team import TeamIssueCommentUI
        return TeamIssueCommentUI(self.team.uid)


class FairIssueUI(TeamIssueUI):
    _q_exports = TeamIssueUI._q_exports + ['relate', 'pledge']

    def __init__(self, issue_id):
        self.target = get_fair()
        self.issue_number = issue_id  # fair issue 直接拿 issue_id 当 number

        self.issue_id = issue_id
        self.issue = Issue.get_cached_issue(issue_id)
        self.issue_template = 'issue/team_issue.html'

    def relate(self, request):
        if request.method == 'POST':
            if request.get_form_var('add'):
                repo = request.get_form_var('repo', '').strip()
                self.issue.add_related_project(repo)
                return request.redirect(self.issue.url)
            for prj in self.issue.related_projects:
                if request.get_form_var('delete_%s' % prj.id, ''):
                    self.issue.delete_related_project(prj)
                    return request.redirect(self.issue.url)
        return st('/fair/relate.html', request=request, issue=self.issue)

    def pledge(self, request):
        if request.method == 'POST':
            amount = request.get_form_var('amount')
            if not amount.isdigit():
                error = '请输入承诺贡献的PR数量'
                return st('/fair/pledge.html', request=request,
                          issue=self.issue, error=error)
            amount = int(amount)
            self.issue.update_pledge(request.user, amount)
            return request.redirect(self.issue.url)
        return st('/fair/pledge.html', request=request, issue=self.issue)
