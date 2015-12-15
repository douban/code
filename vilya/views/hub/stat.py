# -*- coding: utf-8 -*-

from vilya.models.statistics import (
    get_all_ticket,
    get_ticket_comment_count,
    get_all_issue,
    get_issue_comment_count,
    get_all_project,
    get_all_gist
)
from vilya.libs.template import st
from vilya.views.api.utils import jsonize

_q_exports = ['source']


@jsonize
def source(request):
    # pr相关数据
    pr_rs = get_all_ticket()
    pr_count = len(pr_rs)
    pr_open_count = len(filter(lambda x: x[1] is None, pr_rs))

    # issue相关数据
    issue_rs = get_all_issue()
    issue_count = len(issue_rs)
    issue_open_count = len(filter(lambda x: x[1] is None, issue_rs))

    project_rs = get_all_project()
    gist_rs = get_all_gist()

    data = dict(
        # pr相关数据
        pr_count=pr_count,
        pr_open_count=pr_open_count,
        pr_closed_count=pr_count - pr_open_count,
        pr_comment_count=get_ticket_comment_count(),
        # issue相关数据
        issue_count=issue_count,
        issue_open_count=issue_open_count,
        issue_closed_count=issue_count - issue_open_count,
        issue_comment_count=get_issue_comment_count(),
        # project相关数据
        project_count=len(project_rs),
        project_fork_count=len(filter(lambda x: x[1] is not None, project_rs)),
        # gist相关数据
        gist_count=len(gist_rs),
        gist_fork_count=len(filter(lambda x: x[1] != 0, gist_rs))
    )

    return data


def _q_index(request):
    return st('stat.html', **locals())
