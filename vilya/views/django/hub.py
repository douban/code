# -*- coding: utf-8 -*-

import re
import json
from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from vilya.libs.template import st


def emoji(request):
    return HttpResponse(st('emoji.html', **locals()))


def public_timeline(request):
    from vilya.models.feed import get_public_feed, PAGE_ACTIONS_COUNT
    actions = get_public_feed().get_actions(stop=PAGE_ACTIONS_COUNT - 1)
    return HttpResponse(st('public_timeline.html', **locals()))


def yours(request):
    from vilya.models.feed import get_user_feed, PAGE_ACTIONS_COUNT
    from vilya.models.project import CodeDoubanProject
    user = request.user
    actions = (get_user_feed(user.username)
               .get_actions(stop=PAGE_ACTIONS_COUNT - 1))

    your_projects = CodeDoubanProject.get_projects(
        owner=user.username, sortby="lru")
    watched_projects = CodeDoubanProject.get_watched_others_projects_by_user(
        user=user.username, sortby='lru')

    badge_items = user.get_badge_items()
    return HttpResponse(st('my_actions.html', **locals()))


def search(request):
    from vilya.models.project import CodeDoubanProject
    q = request.GET.get('q')
    if q:
        results = CodeDoubanProject.search_by_name(q)
    return HttpResponse(st('search.html', **locals()))

@csrf_exempt
def create(request):
    from datetime import datetime
    from vilya.models.project import CodeDoubanProject
    from vilya.models.consts import (
        ORGANIZATION_PROJECT,
        MIRROR_PROJECT,
        PEOPLE_PROJECT,
        MIRROR_STATE_CLONING,
        MIRROR_NOT_PROXY)
    from vilya.models.mirror import CodeDoubanMirror
    user = request.user
    if not user:
        return request.redirect("/")
    errors = ""

    template_filename = 'create.html'

    if request.method == "POST":
        name = request.POST.get('name')
        product = request.POST.get('product')
        org_proj = request.POST.get('org_proj')
        summary = request.POST.get('summary')
        repo_url = request.POST.get('url')
        fork_from = request.POST.get('fork_from')
        intern_banned = request.POST.get('intern_banned', None)
        with_proxy = request.POST.get('with_proxy', MIRROR_NOT_PROXY)
        with_proxy = int(with_proxy)
        mirror = None

        def add_people_project(project):
            name = "%s/%s" % (project.owner_id, project.name)
            _project = CodeDoubanProject.add(
                name=name, owner_id=project.owner_id,
                summary=project.summary, product=project.product,
                intern_banned=project.intern_banned)
            return _project

        def add_org_project(project):
            _project = CodeDoubanProject.add(
                name=name, owner_id=project.owner_id,
                summary=project.summary, product=project.product,
                intern_banned=project.intern_banned)
            return _project

        def add_mirror_project(project):
            name = "mirror/%s" % (project.name)
            _project = CodeDoubanProject.add(
                name=name, owner_id='mirror', summary=project.summary,
                product=project.product, intern_banned=project.intern_banned,
                mirror=project.mirror_url)
            if _project:
                CodeDoubanMirror.add(url=project.mirror_url,
                                     state=MIRROR_STATE_CLONING,
                                     project_id=_project.id,
                                     with_proxy=project.mirror_proxy)
            return _project

        def add_fork_project(project):
            name = "%s/%s" % (project.owner_id, project.name)
            _project = CodeDoubanProject.add(
                name=name, owner_id=project.owner_id, summary=project.summary,
                product=project.product, fork_from=project.fork_from,
                intern_banned=project.intern_banned)
            if _project:
                fork_from_project = CodeDoubanProject.get(project.fork_from)
                _project.update(project.summary,
                                project.product,
                                name,
                                fork_from_project.intern_banned)
            return _project

        def validate_project(project_type, project):
            error = ''
            if project_type in (PEOPLE_PROJECT, ORGANIZATION_PROJECT):
                error = project.validate()
            elif project_type == MIRROR_PROJECT:
                error = project.validate()
                if not error:
                    error = CodeDoubanMirror.validate(project.mirror_url)
            else:
                error = project.validate()
            return error

        def add_project(project):
            _project = None
            if project_type == PEOPLE_PROJECT:
                _project = add_people_project(project)
            elif project_type == ORGANIZATION_PROJECT:
                _project = add_org_project(project)
            elif project_type == MIRROR_PROJECT:
                _project = add_mirror_project(project)
            else:
                _project = add_fork_project(project)
            return _project

        project = CodeDoubanProject(None, name, user.username, summary,
                                    datetime.now(), product, None, None,
                                    fork_from=fork_from,
                                    intern_banned=intern_banned,
                                    mirror_url=repo_url,
                                    mirror_proxy=with_proxy)
        # FIXME: rename org_proj of html
        project_type = org_proj
        errors = validate_project(project_type, project)
        if errors:
            return HttpResponse(st(template_filename, **locals()))

        project = add_project(project)
        if not project:
            fork_from = ''
            errors = 'project exists'
            return HttpResponse(st(template_filename, **locals()))

        CodeDoubanProject.add_watch(project.id, user.name)
        return HttpResponseRedirect('/%s/' % project.name)

    fork_from = ''
    if request.POST.get('fork_from'):
        fork_from = CodeDoubanProject.get(request.POST.get('fork_from'))
        name = "%s/%s" % (user.name, fork_from.realname)
        if CodeDoubanProject.exists(name):
            return HttpResponseRedirect('/%s/' % name)
        projects = CodeDoubanProject.gets_by_owner_id(user.name)
        for p in projects:
            if p.origin_project_id == fork_from.id and '/' in p.name:
                return HttpResponseRedirect('/%s/' % p.name)
    return HttpResponse(st(template_filename, **locals()))


def future(request):
    return HttpResponse(st('future.html', **locals()))


# TODO(xutao) move to /teams/new
@csrf_exempt
def add_team(request):
    from vilya.libs.signals import team_created_signal
    from vilya.models.consts import TEAM_OWNER
    from vilya.models.user import User
    from vilya.models.team import Team
    user = request.user
    if not user:
        return HttpResponseRedirect("/")

    errors = ""
    uid = request.POST.get('uid') or ''
    name = request.POST.get('name') or ''
    description = request.POST.get('description') or ''
    if request.method == "POST":

        teams = Team.gets()
        team_uid_pattern = re.compile(r'[a-zA-Z0-9\_]*')
        if not uid:
            error = 'uid_not_exists'
        elif not name:
            error = 'name_not_exists'
        elif uid != re.findall(team_uid_pattern, uid)[0]:
            error = 'invilid_uid'
        elif uid in [team.uid for team in teams]:
            error = 'uid_existed'
        elif User.check_exist(uid):
            error = 'user_id_existed'
        elif name in [team.name for team in teams]:
            error = 'name_existed'
        else:
            team = Team.add(uid, name, description)
            if team:
                team_created_signal.send(user.name,
                                         team_name=team.name,
                                         team_uid=team.uid)
                team.add_user(user, TEAM_OWNER)
                return HttpResponseRedirect(team.url)

    return HttpResponse(st('/teams/add_team.html', **locals()))


def beacon(request, path):
    if not path:
        return HttpResponseRedirect('/hub/notification')

    from vilya.models.user import User
    from vilya.models.notification import Notification
    # cat hook.gif | base64
    EMAIL_HOOK_GIF = "R0lGODlhAQABAID/AP///wAAACwAAAAAAQABAAACAkQBADs="

    url = path
    parts = url.split('.')
    if len(parts) == 2 and parts[1] == 'gif':
        uid, ext = parts
        username = request.GET.get('user')
        user = User(username) if username else request.user
    else:
        raise Http404()

    if user and uid:
        tokens = uid.split('-')
        if tokens[0] == 'pullrequest':
            project_name = '-'.join(tokens[1:-2])
            pull_number = tokens[-2]
            Notification.mark_as_read_by_pull(
                user.name, project_name, pull_number)
        else:
            Notification.mark_as_read(user.name, uid)

    response = StreamingHttpResponse(content_type='image/gif')
    response.streaming_content = EMAIL_HOOK_GIF.decode('base64')
    return response


def my_issues_filter(list_type):
    from vilya.models.project_issue import ProjectIssue
    from vilya.models.project import CodeDoubanProject
    ISSUES_COUNT_PER_PAGE = 25

    def index(request):
        user = request.user
        my_issues = []
        if user:
            page = request.GET.get('page', 1)
            state = request.GET.get("state", "open")
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
        return HttpResponse(st('issue/my_issues.html', **locals()))
    return index


my_issues = my_issues_filter('repos')
my_issues_assigned = my_issues_filter('assigned')
my_issues_created_by = my_issues_filter('created_by')
my_issues_participated = my_issues_filter('participated')


def my_pull_requests(request):
    from random import shuffle
    from vilya.models.consts import MY_PULL_REQUESTS_TAB_INFO

    user = request.user
    if user:
        list_type = request.GET.get("list_type", "invited")

        n_invited = user.n_open_invited
        n_participated = user.n_open_participated
        n_yours = user.n_user_open_submit_pull_requests
        counts = [n_invited, n_participated, n_yours, None]
        tab_info = []
        for tab, count in zip(MY_PULL_REQUESTS_TAB_INFO, counts):
            tab.update(count=count)
            tab_info.append(tab)

        if list_type == "participated":
            tickets = user.get_participated_pull_requests()
        elif list_type == "yours":
            tickets = user.get_user_submit_pull_requests()
        elif list_type == "explore":
            from vilya.models.ticket import Ticket
            tickets = Ticket.gets_all_opened()
            ticket_total_len = len(tickets)
            shuffle(tickets)
        else:
            tickets = user.get_invited_pull_requests()
        is_closed_tab = False
        ticket_total_len = len(tickets)
        return HttpResponse(st('my_pull_requests.html', **locals()))


def notification(request):
    from vilya.models.notification import Notification
    from vilya.models.actions.base import ActionScope
    from vilya.models.actions import migrate_notif_data
    user = request.user
    if user:
        all = request.POST.get('all')
        scope = request.POST.get('scope')
        unread = not all or all != '1'
        scope = ActionScope.getScope(scope) or ''  # 不带scope则默认所有

        actions = Notification.get_data(user.name)

        # 迁移数据
        all_actions = [migrate_notif_data(action, user.name)
                       for action in actions]

        if scope:
            actions = [action for action in all_actions
                       if action.get('scope') == scope]
        else:
            actions = all_actions

        if unread:
            actions = [action for action in actions if not action.get('read')]
            count_dict = {s: len([a for a in all_actions
                          if a.get('scope') == s and not a.get('read')])
                          for s in ActionScope.all_scopes}
        else:
            count_dict = {s: len([a for a in all_actions
                          if a.get('scope') == s])
                          for s in ActionScope.all_scopes}
        count_dict['all'] = sum(count_dict.values())

        return HttpResponse(st('notifications.html', **locals()))
    else:
        return HttpResponseRedirect("/hub/teams")


@csrf_exempt
def notification_mark(request):
    ''' mark by uids '''
    from vilya.models.notification import Notification
    user = request.user
    if user:
        uids = request.POST.get('uids', [])
        if isinstance(uids, basestring):
            uids = [uids]
        for uid in uids:
            Notification.mark_as_read(user.name, uid)
        return HttpResponse(json.dumps(dict(r=0)))
    else:
        return HttpResponse(json.dumps(dict(r=1)))


def notification_read_all(request):
    ''' mark all '''
    from vilya.models.notification import Notification
    user = request.user
    if user:
        Notification.mark_all_as_read(user.name)
        return HttpResponseRedirect('/hub/notification')
    else:
        return HttpResponseRedirect("/hub/teams")


@csrf_exempt
def notification_mute(request):
    ''' mute ticket(pr) or issue, just 'project' scope yet. '''
    from vilya.models.mute import Mute
    from vilya.models.project_issue import ProjectIssue
    user = request.user
    if user:
        entry_type = request.POST.get('type', '')
        target = request.POST.get('target', '')
        entry_id = request.POST.get('id', '')
        if entry_type == 'pull':
            Mute.mute('ticket', target, entry_id, user)
        elif entry_type == 'issue':
            # TODO: models.issue.leave or mute
            issue = ProjectIssue.get_by_proj_name_and_number(target, entry_id)
            if user.name != issue.creator_id:
                issue.delete_participant(user.name)
        return HttpResponse(json.dumps(dict(r=0)))
    else:
        return HttpResponse(json.dumps(dict(r=1)))


def notification_notification(request, id):
    from vilya.models.notification import Notification
    user = request.user
    if id:
        Notification.mark_as_read(user.name, id)
    url = request.GET.get('url')
    # TODO fix request.query.url
    return HttpResponseRedirect(url)


def stat_index(request):
    return HttpResponse(st('stat.html', **locals()))


def stat_source(request):
    from vilya.models.statistics import (
        get_all_ticket,
        get_ticket_comment_count,
        get_all_issue,
        get_issue_comment_count,
        get_all_project,
        get_all_gist
    )
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

    return HttpResponse(json.dumps(data))
