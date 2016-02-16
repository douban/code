# -*- coding: utf-8 -*-

import json
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from vilya.libs.template import st

from vilya.views.django.issue import IssueView


def issue(request, name, id):
    from vilya.models.team import Team
    from vilya.models.team_issue import TeamIssue
    from vilya.models.issue import Issue
    target = Team.get_by_uid(name)
    issue_number = id
    team_issue = TeamIssue.get(target.id, number=issue_number)
    issue_id = team_issue.issue_id
    issue = Issue.get_cached_issue(issue_id)
    issue_template = 'issue/team_issue.html'
    return IssueView(request, target, issue, id, issue_template).index()


@csrf_exempt
def issue_upvote(request, name, id):
    from vilya.models.team import Team
    from vilya.models.team_issue import TeamIssue
    from vilya.models.issue import Issue
    target = Team.get_by_uid(name)
    issue_number = id
    team_issue = TeamIssue.get(target.id, number=issue_number)
    issue_id = team_issue.issue_id
    issue = Issue.get_cached_issue(issue_id)
    return IssueView(request, target, issue, id, '').upvote()


@csrf_exempt
def issue_comment(request, name, id):
    from vilya.models.team import Team
    from vilya.models.team_issue import TeamIssue
    from vilya.models.issue import Issue
    target = Team.get_by_uid(name)
    issue_number = id
    team_issue = TeamIssue.get(target.id, number=issue_number)
    issue_id = team_issue.issue_id
    issue = Issue.get_cached_issue(issue_id)
    return IssueView(request, target, issue, id, '').comment()


@csrf_exempt
def issue_tag(request, name, id):
    from vilya.models.team import Team
    from vilya.models.team_issue import TeamIssue
    from vilya.models.issue import Issue
    target = Team.get_by_uid(name)
    issue_number = id
    team_issue = TeamIssue.get(target.id, number=issue_number)
    issue_id = team_issue.issue_id
    issue = Issue.get_cached_issue(issue_id)
    return IssueView(request, target, issue, id, '').tag()


@csrf_exempt
def issue_milestone(request, name, id):
    from vilya.models.team import Team
    from vilya.models.team_issue import TeamIssue
    from vilya.models.issue import Issue
    target = Team.get_by_uid(name)
    issue_number = id
    team_issue = TeamIssue.get(target.id, number=issue_number)
    issue_id = team_issue.issue_id
    issue = Issue.get_cached_issue(issue_id)
    return IssueView(request, target, issue, id, '').milestone()


@csrf_exempt
def issue_join(request, name, id):
    from vilya.models.team import Team
    from vilya.models.team_issue import TeamIssue
    from vilya.models.issue import Issue
    target = Team.get_by_uid(name)
    issue_number = id
    team_issue = TeamIssue.get(target.id, number=issue_number)
    issue_id = team_issue.issue_id
    issue = Issue.get_cached_issue(issue_id)
    return IssueView(request, target, issue, id, '').join()


@csrf_exempt
def issue_leave(request, name, id):
    from vilya.models.team import Team
    from vilya.models.team_issue import TeamIssue
    from vilya.models.issue import Issue
    target = Team.get_by_uid(name)
    issue_number = id
    team_issue = TeamIssue.get(target.id, number=issue_number)
    issue_id = team_issue.issue_id
    issue = Issue.get_cached_issue(issue_id)
    return IssueView(request, target, issue, id, '').leave()


@csrf_exempt
def issue_assign(request, name, id):
    from vilya.models.team import Team
    from vilya.models.team_issue import TeamIssue
    from vilya.models.issue import Issue
    target = Team.get_by_uid(name)
    issue_number = id
    team_issue = TeamIssue.get(target.id, number=issue_number)
    issue_id = team_issue.issue_id
    issue = Issue.get_cached_issue(issue_id)
    return IssueView(request, target, issue, id, '').assign()


@csrf_exempt
def comment_edit(request, name, id):
    from vilya.models.team import Team
    from vilya.models.issue_comment import IssueComment
    target = Team.get_by_uid(name)
    comment = IssueComment.get(id)

    user = request.user
    current_user = request.user
    if request.method == 'POST':
        if comment.author_id != user.username:
            return HttpResponseForbidden()
        content = request.POST.get(
            'pull_request_comment', '').decode('utf-8')
        comment.update(content)
        comment = IssueComment.get(comment.id)
        author = user
        return HttpResponse(json.dumps(dict(
            r=0,
            html=st('/widgets/issue/issue_comment.html', **locals()))))


@csrf_exempt
def comment_delete(request, name, id):
    from vilya.models.issue import Issue
    from vilya.models.issue_comment import IssueComment
    comment = IssueComment.get(id)

    user = request.user
    if comment.author_id != user.username:
        return HttpResponseForbidden()
    issue_id = comment.issue_id
    ok = comment.delete()
    if not ok:
        return HttpResponse(json.dumps({'r': 0}))
    pissue = Issue.get_cached_issue(issue_id)
    pissue.update_rank_score()
    return HttpResponse(json.dumps({'r': 1}))
