# -*- coding: utf-8 -*-

from vilya.libs.template import st
from vilya.models.project_issue import ProjectIssue
from vilya.models.project import CodeDoubanProject

ISSUES_COUNT_PER_PAGE = 25
_q_exports = ['assigned', 'created_by', 'participated']


def _filter(list_type):
    def index(request):
        user = request.user
        my_issues = []
        if user:
            page = request.get_form_var('page', 1)
            state = request.get_form_var("state", "open")
            is_closed_tab = None if state == "open" else True
            project_ids = CodeDoubanProject.get_ids(user.name)
            # TODO: 下面的这些N，可以考虑先从 get 参数里拿一下，没有的话再重新读
            n_repos_issue = ProjectIssue.get_count_by_project_ids(project_ids,
                                                                  state)
            n_assigned_issue = user.get_count_assigned_issues(state)
            n_created_issue = user.get_count_created_issues(state)
            n_participated_issue = user.get_n_participated_issues(state)
            total_issues = {
                'repos': n_repos_issue,
                'assigned': n_assigned_issue,
                'created_by': n_created_issue,
                'participated': n_participated_issue,
            }[list_type]
            n_pages = (total_issues - 1) / ISSUES_COUNT_PER_PAGE + 1
            dt = {
                'state': state,
                'limit': ISSUES_COUNT_PER_PAGE,
                'start': ISSUES_COUNT_PER_PAGE * (int(page) - 1),
            }
            if list_type == 'repos':
                my_issues = ProjectIssue.gets_by_project_ids(project_ids, **dt)
            else:
                get_my_issues = {
                    'assigned': user.get_assigned_issues,
                    'created_by': user.get_created_issues,
                    'participated': user.get_participated_issues,
                }[list_type]
                my_issues = get_my_issues(**dt)
        return st('issue/my_issues.html', **locals())
    return index

_q_index = _filter('repos')
assigned = _filter('assigned')
created_by = _filter('created_by')
participated = _filter('participated')
