# -*- coding: utf-8 -*-

import json
from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from vilya.libs.template import st
from vilya.views.django.issue import IssueView


def _issues_filter(list_type):
    ''' filter repo, created_by, assigned, search 4 list types. '''
    def index(request, username, projectname):
        from vilya.models.elastic import SearchEngine
        from vilya.models.elastic.issue_pr_search import IssueSearch
        from vilya.models.project import CodeDoubanProject
        from vilya.models.project_issue import ProjectIssue
        from vilya.models.tag import TagName
        from vilya.models.milestone import Milestone
        ISSUES_COUNT_PER_PAGE = 25
        if list_type == 'search':
            key_word = request.GET.get('q', None)
            if not key_word:
                return issues_index(request, username, projectname)

        _name = '/'.join([username, projectname])
        project = CodeDoubanProject.get_by_name(_name)

        milestone_number = request.GET.get('milestone')
        state = request.GET.get('state', 'open')
        page = request.GET.get('page', 1)
        project_name = _name
        user = request.user
        response = HttpResponse()
        order = get_order_type(request, response, 'project_issues_order')  # noqa 目前支持list_type = repo的sort_by
        n_open_issues = project.n_open_issues
        n_closed_issues = project.n_closed_issues
        n_everyone_issues = 0
        n_assigned_issues = 0
        n_created_issues = 0
        n_pages = 0
        selected_tag_names = request.GET.get('tags', '')
        start = ISSUES_COUNT_PER_PAGE * (int(page) - 1)
        limit = ISSUES_COUNT_PER_PAGE

        is_closed_tab = None if state == "open" else True
        issue_list = []
        total_issues = 0
        opts = dict(project=project, state=state, start=start,
                    limit=limit, order=order)
        if selected_tag_names:
            selected_tag_names = selected_tag_names.split(',')
            tags = filter(None, [TagName.get_project_issue_tag(
                name, project) for name in selected_tag_names])
            opts['tags'] = tags
        show_tags = project.get_group_tags(selected_tag_names)

        if milestone_number:
            milestone = Milestone.get_by_project(
                project, number=milestone_number)
            opts['milestone'] = milestone

        # FIXME: why user or list_type ?
        if user or list_type in ('repo', 'search'):
            if list_type == 'search':
                # FIXME: search with assigned or creator
                search_result = IssueSearch.search_a_phrase(
                    key_word, project.id,
                    size=n_open_issues + n_closed_issues,
                    state=state) or []
                search_issue_ids = []
                if search_result and not search_result.get('error'):
                    search_issue_ids = [
                        id for id, in SearchEngine.decode(
                            search_result, ['issue_id'])]
                # FIXME: is search_issue_ids int[]?
                opts['issue_ids'] = search_issue_ids
            elif list_type == 'created_by':
                opts['creator'] = user
            elif list_type == 'assigned':
                opts['assignee'] = user
            # FIXME: update n_closed_issues & n_open_issues
            multi_dict = ProjectIssue.get_multi_by(**opts)
            issue_list = multi_dict['issues']
            total_issues = multi_dict['total']

            if user:
                if list_type == 'repo':
                    n_assigned_issues = user.get_n_assigned_issues_by_project(project.id, state)  # noqa
                    n_created_issues = user.get_n_created_issues_by_project(project.id, state)  # noqa
                elif list_type == 'created_by':
                    n_assigned_issues = user.get_n_assigned_issues_by_project(project.id, state)  # noqa
                    n_created_issues = total_issues
                elif list_type == 'assigned':
                    n_assigned_issues = total_issues
                    n_created_issues = user.get_n_created_issues_by_project(project.id, state)  # noqa
                elif list_type == 'search' and search_issue_ids:
                    n_assigned_issues = ProjectIssue.get_n_by_issue_ids_and_assignee_id(  # noqa
                        search_issue_ids, state, user.name)
                    n_created_issues = ProjectIssue.get_n_by_issue_ids_and_creator_id(  # noqa
                        search_issue_ids, state, user.name)
            n_pages = (total_issues - 1) / ISSUES_COUNT_PER_PAGE + 1

        # tags 的选择只会改变选中的filter的显示issue数
        if list_type in ('repo', 'search'):
            n_everyone_issues = total_issues
        else:
            n_everyone_issues = n_open_issues \
                if state == "open" else n_closed_issues
        response.content = st('issue/issues.html', **locals())
        return response
    return index


issues_index = _issues_filter('repo')
issues_created_by = _issues_filter('created_by')
issues_assigned = _issues_filter('assigned')
issues_search = _issues_filter('search')


def get_order_type(request, response, cookie_name):
    ''' order cookie getter/setter '''
    cookie_order = request.COOKIES.get(cookie_name)
    order = request.GET.get('order', cookie_order)
    if order != 'hot':
        order = 'date'
    if order != cookie_order:
        response.set_cookie(cookie_name,
                            order,
                            expires="Thu 01-Jan-2020 00:00:00 GMT")
    return order


def issues_new(request, username, projectname):
    from vilya.models.team import Team
    from vilya.models.project import CodeDoubanProject
    name = '/'.join([username, projectname])
    project = CodeDoubanProject.get_by_name(name)
    project_name = name

    user = request.user
    tags = project.tags
    error = request.GET.get('error')
    teams = Team.get_all_team_uids()
    return HttpResponse(st('issue/new.html', **locals()))


@csrf_exempt
def issues_create(request, username, projectname):
    from dispatches import dispatch
    from vilya.libs.signals import issue_signal
    from vilya.models.project_issue import ProjectIssue
    from vilya.models.project import CodeDoubanProject
    name = '/'.join([username, projectname])
    project = CodeDoubanProject.get_by_name(name)
    project_name = name

    if request.method == 'POST':
        user = request.user
        if not user:
            raise Http404()
        project = request.POST.get('project')
        title = request.POST.get('title', '').decode('utf-8')
        description = request.POST.get('body', '').decode('utf-8')
        tags = request.POST.get('issue_tags', [])
        if isinstance(tags, list):
            tags = [tag.decode('utf-8') for tag in tags if tag]
        elif isinstance(tags, basestring):
            tags = [tags.decode('utf-8')]

        if not project:
            raise Http404()
        if not title.strip():
            return HttpResponseRedirect('/%s/issues/new?error=empty' % project)
        project = CodeDoubanProject.get_by_name(project)
        pissue = ProjectIssue.add(title, description, user.name,
                                    project=project.id)
        pissue.add_tags(tags, pissue.project_id)
        # TODO: 重构feed后取消信号发送
        issue_signal.send(author=user.name, content=description,
                            issue_id=pissue.issue_id)
        dispatch('issue', data={
            'sender': user.name,
            'content': description,
            'issue': pissue
        })
        return HttpResponseRedirect(pissue.url)
    return HttpResponseRedirect('/%s/issues' % project_name)


def issues_metioned(request, username, projectname):
    from vilya.models.project import CodeDoubanProject
    name = '/'.join([username, projectname])
    project = CodeDoubanProject.get_by_name(name)

    list_type = 'mentioned'
    state = request.GET.get('state', 'open')
    page = request.GET.get('page', 1)
    project_name = name
    user = request.user
    n_open_issues = project.n_open_issues
    n_closed_issues = project.n_closed_issues
    n_everyone_issues = 0
    n_assigned_issues = 0
    n_created_issues = 0
    n_mentioned_issues = 0
    n_pages = 0
    issue_list = []
    total_issues = 0
    is_closed_tab = None if state == "open" else True
    if user:
        n_assigned_issues = user.get_n_assigned_issues_by_project(project.id, state)  # noqa
        n_created_issues = user.get_n_created_issues_by_project(project.id, state)  # noqa
    n_everyone_issues = n_open_issues \
        if state == "open" else n_closed_issues
    return HttpResponse(st('issue/issues.html', **locals()))


def issues_milestones(request, username, projectname):
    from vilya.models.project import CodeDoubanProject
    name = '/'.join([username, projectname])
    project = CodeDoubanProject.get_by_name(name)
    milestones = project.issue_milestones
    return HttpResponse(st('/issue/milestones.html', **locals()))


def issue(request, username, projectname, id):
    from vilya.models.issue import Issue
    from vilya.models.project_issue import ProjectIssue
    from vilya.models.project import CodeDoubanProject
    name = '/'.join([username, projectname])
    target = CodeDoubanProject.get_by_name(name)
    issue_number = id
    project_issue = ProjectIssue.get(target.id,
                                     number=issue_number)
    issue_id = project_issue.issue_id
    issue = Issue.get_cached_issue(issue_id)
    issue_template = 'issue/issue.html'

    return IssueView(request, target, issue, id, issue_template).index()


@csrf_exempt
def issue_upvote(request, username, projectname, id):
    from vilya.models.issue import Issue
    from vilya.models.project_issue import ProjectIssue
    from vilya.models.project import CodeDoubanProject
    name = '/'.join([username, projectname])
    target = CodeDoubanProject.get_by_name(name)
    issue_number = id
    project_issue = ProjectIssue.get(target.id,
                                     number=issue_number)
    issue_id = project_issue.issue_id
    issue = Issue.get_cached_issue(issue_id)

    return IssueView(request, target, issue, id, '').upvote()


@csrf_exempt
def issue_comment(request, username, projectname, id):
    from vilya.models.issue import Issue
    from vilya.models.project_issue import ProjectIssue
    from vilya.models.project import CodeDoubanProject
    name = '/'.join([username, projectname])
    target = CodeDoubanProject.get_by_name(name)
    issue_number = id
    project_issue = ProjectIssue.get(target.id,
                                     number=issue_number)
    issue_id = project_issue.issue_id
    issue = Issue.get_cached_issue(issue_id)
    return IssueView(request, target, issue, id, '').comment()



@csrf_exempt
def issue_tag(request, username, projectname, id):
    from vilya.models.issue import Issue
    from vilya.models.project_issue import ProjectIssue
    from vilya.models.project import CodeDoubanProject
    name = '/'.join([username, projectname])
    target = CodeDoubanProject.get_by_name(name)
    issue_number = id
    project_issue = ProjectIssue.get(target.id,
                                     number=issue_number)
    issue_id = project_issue.issue_id
    issue = Issue.get_cached_issue(issue_id)
    return IssueView(request, target, issue, id, '').tag()


@csrf_exempt
def issue_milestone(request, username, projectname, id):
    from vilya.models.issue import Issue
    from vilya.models.project_issue import ProjectIssue
    from vilya.models.project import CodeDoubanProject
    name = '/'.join([username, projectname])
    target = CodeDoubanProject.get_by_name(name)
    issue_number = id
    project_issue = ProjectIssue.get(target.id,
                                     number=issue_number)
    issue_id = project_issue.issue_id
    issue = Issue.get_cached_issue(issue_id)
    return IssueView(request, target, issue, id, '').milestone()


@csrf_exempt
def issue_join(request, username, projectname, id):
    from vilya.models.issue import Issue
    from vilya.models.project_issue import ProjectIssue
    from vilya.models.project import CodeDoubanProject
    name = '/'.join([username, projectname])
    target = CodeDoubanProject.get_by_name(name)
    issue_number = id
    project_issue = ProjectIssue.get(target.id,
                                     number=issue_number)
    issue_id = project_issue.issue_id
    issue = Issue.get_cached_issue(issue_id)
    return IssueView(request, target, issue, id, '').join()


@csrf_exempt
def issue_leave(request, username, projectname, id):
    from vilya.models.issue import Issue
    from vilya.models.project_issue import ProjectIssue
    from vilya.models.project import CodeDoubanProject
    name = '/'.join([username, projectname])
    target = CodeDoubanProject.get_by_name(name)
    issue_number = id
    project_issue = ProjectIssue.get(target.id,
                                     number=issue_number)
    issue_id = project_issue.issue_id
    issue = Issue.get_cached_issue(issue_id)
    return IssueView(request, target, issue, id, '').leave()


@csrf_exempt
def issue_assign(request, username, projectname, id):
    from vilya.models.issue import Issue
    from vilya.models.project_issue import ProjectIssue
    from vilya.models.project import CodeDoubanProject
    name = '/'.join([username, projectname])
    target = CodeDoubanProject.get_by_name(name)
    issue_number = id
    project_issue = ProjectIssue.get(target.id,
                                     number=issue_number)
    issue_id = project_issue.issue_id
    issue = Issue.get_cached_issue(issue_id)
    return IssueView(request, target, issue, id, '').assign()


@csrf_exempt
def issues_tags_tag(request, username, projectname, name):
    from vilya.models.tag import TagName
    from vilya.models.project import CodeDoubanProject
    project_name = '/'.join([username, projectname])
    target = CodeDoubanProject.get_by_name(project_name)

    target_type = target.tag_type
    target_id = target.id

    tag = TagName.get_by_name_and_target_id(name, target_type, target_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        # TODO: check name
        if name and tag.name != name:
            tag.update_name(name)
        color = request.POST.get('color')
        # color: #xxxxxx
        # TODO: check color
        if color and tag.hex_color != color[1:]:
            tag.update_color(color[1:])
    return HttpResponseRedirect(target.url + 'issues')


@csrf_exempt
def issue_comments_comment_edit(request, username, projectname, id):
    from vilya.models.issue_comment import IssueComment
    from vilya.models.project import CodeDoubanProject
    project_name = '/'.join([username, projectname])
    project = CodeDoubanProject.get_by_name(project_name)
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
        target = project
        return HttpResponse(json.dumps(dict(
            r=0,
            html=st('/widgets/issue/issue_comment.html', **locals()))))


@csrf_exempt
def issue_comments_comment_delete(request, username, projectname, id):
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
