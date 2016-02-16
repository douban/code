# -*- coding: utf-8 -*-

import re
import json
import requests
from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from vilya.libs.template import st


def team_index(request, name):
    from vilya.models.team import Team
    team_uid = name
    user = request.user
    team = Team.get_by_uid(team_uid)
    if not team:
        raise Http404()
    projects = team.projects
    is_admin = False
    if user and team.is_owner(user.name):
        is_admin = True
    return HttpResponse(st('/teams/team.html', **locals()))


def team_join(request, name):
    from vilya.libs.signals import team_joined_signal
    from vilya.models.consts import TEAM_MEMBER
    from vilya.models.team import Team
    user = request.user
    team_uid = name
    team = Team.get_by_uid(team_uid)
    if not user or not team:
        return HttpResponse(json.dumps(dict(r=1)))

    team.add_user(user, TEAM_MEMBER)
    team_joined_signal.send(user.name,
                            team_id=team.id,
                            team_uid=team.uid,
                            team_name=team.name)
    return HttpResponse(json.dumps(dict(r=0)))


@csrf_exempt
def team_upload_profile(request, name):
    from vilya.models.consts import UPLOAD_URL
    from vilya.models.team import Team
    user = request.user
    team_uid = name
    team = Team.get_by_uid(team_uid)
    if not user and not team:
        return HttpResponse(json.dumps(dict(r=1)))
    if team and not team.is_owner(user.name):
        return HttpResponse(json.dumps(dict(r=1)))

    upload_url = request.POST.get('url', '')
    hash_png = request.POST.get('hash', '')
    profile = {'origin': upload_url}
    if upload_url and hash_png:
        # FIXME(xutao) remove useless UPLOAD_URL
        rsize_url = '{0}/r/{1}?w=100&h=100'.format(UPLOAD_URL, hash_png)
        r = requests.get(rsize_url)
        r.raise_for_status()
        profile.update({'icon': r.text})
    team.profile = profile
    return HttpResponse(json.dumps(dict(r=0)))

def team_leave(request, name):
    from vilya.models.team import Team
    user = request.user
    team_uid = name
    team = Team.get_by_uid(team_uid)
    if not user or not team:
        return HttpResponse(json.dumps(dict(r=1)))

    team.remove_user(user)
    return HttpResponse(json.dumps(dict(r=0)))


@csrf_exempt
def team_add_project(request, name):
    from vilya.models.project import CodeDoubanProject
    from vilya.models.team import Team
    user = request.user
    team_uid = name
    team = Team.get_by_uid(team_uid)
    if not user and not team:
        return HttpResponseRedirect('/')
    if team and not team.is_owner(user.name):
        return HttpResponseRedirect(team.url)

    project_name = request.POST.get('project_name') or ''
    project = CodeDoubanProject.get_by_name(project_name)
    error = ''
    if request.method == 'POST':
        if not project_name:
            error = 'project_name_not_exists'
        elif not project:
            error = 'project_not_exists'
        else:
            team.add_project(project)
            return HttpResponseRedirect(team.url)
    return HttpResponse(st('/teams/team_add_project.html', **locals()))


@csrf_exempt
def team_remove_project(request, name):
    from vilya.models.project import CodeDoubanProject
    from vilya.models.team import Team
    user = request.user
    team_uid = name
    team = Team.get_by_uid(team_uid)
    if not user or not team:
        return HttpResponse(json.dumps(dict(r=1)))

    if not team.is_owner(user.name):
        return HttpResponse(json.dumps(dict(r=1)))

    project_name = request.POST.get('project_name', '')
    project = CodeDoubanProject.get_by_name(project_name)
    if not project:
        return HttpResponse(json.dumps(dict(r=1)))

    team.remove_project(project)
    return HttpResponse(json.dumps(dict(r=0)))


def team_add_user(request, name):
    from vilya.libs.signals import team_add_member_signal
    from vilya.models.user import User
    from vilya.models.consts import TEAM_IDENTITY_INFO
    from vilya.models.team import Team, TeamUserRelationship
    user = request.user
    team_uid = name
    team = Team.get_by_uid(team_uid)
    if not user or not team:
        return HttpResponse(json.dumps(dict(r=1, error="team不存在")))

    user_id = request.POST.get('user_id', '')
    identity = int(request.POST.get('identity', 0))

    if not team.is_owner(user.name) \
            or identity not in TEAM_IDENTITY_INFO.keys():
        return HttpResponse(json.dumps(dict(r=1, error="没有权限")))

    rl = TeamUserRelationship.get(team_id=team.id, user_id=user_id)
    if not rl:
        team.add_user(User(user_id), identity)
    elif identity == rl.identity:
        return HttpResponse(json.dumps(dict(r=1, error="该用户已存在")))
    elif rl.is_owner and team.n_owners == 1:
        return HttpResponse(json.dumps(dict(r=1, error="只剩一个creator, 不能改变身份")))
    else:
        rl.identity = identity
        rl.save()

    avatar_url = User(user_id).avatar_url
    team_add_member_signal.send(
        user.name, team_uid=team.uid, team_name=team.name,
        receiver=user_id, identity=TEAM_IDENTITY_INFO[identity]["name"])
    return HttpResponse(json.dumps(dict(r=0, uid=user_id, avatar_url=avatar_url)))


@csrf_exempt
def team_remove_user(request, name):
    from vilya.models.team import Team, TeamUserRelationship
    team_uid = name
    user = request.user
    if not user:
        return HttpResponse(json.dumps(dict(r=1, error="用户未登录")))

    team = Team.get_by_uid(team_uid)
    if not team:
        return HttpResponse(json.dumps(dict(r=1, error="team不存在")))

    user_id = request.POST.get('user_id', '')

    if not team.is_owner(user.name):
        return HttpResponse(json.dumps(dict(r=1, error="没有权限")))
    rl = TeamUserRelationship.get(team_id=team.id, user_id=user_id)
    if not rl:
        return HttpResponse(json.dumps(dict(r=1, error="用户未加入team")))
    elif rl.is_owner and team.n_owners == 1:
        return HttpResponse(json.dumps(dict(r=1, error="只剩一个creator不能删除")))
    else:
        rl.delete()
    return HttpResponse(json.dumps(dict(r=0)))


def team_remove(request, name):
    from vilya.models.team import Team
    team_uid = name
    team = Team.get_by_uid(team_uid)
    if not team:
        return HttpResponse(json.dumps(dict(r=1)))

    user = request.user
    if not user or not team.is_owner(user.name):
        return HttpResponse(json.dumps(dict(r=1)))

    team.delete()
    return HttpResponse(json.dumps({'r': 0}))


def team_news(request, name):
    from vilya.models.feed import get_team_feed, PAGE_ACTIONS_COUNT
    from vilya.models.team import Team
    user = request.user
    team_uid = name
    team = Team.get_by_uid(team_uid)
    if not team:
        raise Http404()
    feed = get_team_feed(team.id)
    actions = feed.get_actions(stop=PAGE_ACTIONS_COUNT - 1)
    projects = team.projects
    is_admin = False
    if user and team.is_owner(user.name):
        is_admin = True
    return HttpResponse(st('/teams/news.html', **locals()))


@csrf_exempt
def team_settings(request, name):
    from vilya.models.team import Team
    user = request.user
    team_uid = name
    team = Team.get_by_uid(team_uid)
    if not team:
        raise Http404()
    projects = team.projects

    input_uid = request.POST.get('uid', '')
    input_name = request.POST.get('name', '')
    input_description = request.POST.get('description', '')

    error = ''
    if request.method == "POST":
        if not user:
            return HttpResponseRedirect("/")

        if not team.is_owner(user.name):
            return HttpResponseRedirect(team.url)

        teams = Team.gets()
        team_uid_pattern = re.compile(r'[a-zA-Z0-9\_]*')
        if not input_uid:
            error = 'uid_not_exists'
        elif not input_name:
            error = 'name_not_exists'
        elif input_uid != re.findall(team_uid_pattern, input_uid)[0]:
            error = 'invilid_uid'
        elif input_uid in [t.uid for t in teams] and team.uid != input_uid:
            error = 'uid_existed'
        elif input_name in [t.name for t in teams] \
                and team.name != input_name:
            error = 'name_existed'
        else:
            team.update(input_uid, input_name, input_description)
            return HttpResponseRedirect("/hub/team/%s/settings" % input_uid)
    return HttpResponse(st('/teams/team_settings.html', **locals()))


def team_pulls(request, name):
    from vilya.models.team import Team
    from vilya.models.ticket import Ticket
    TICKETS_COUNT_PER_PAGE = 30
    team_name = name
    team = Team.get_by_uid(team_name)
    user = request.user
    page = request.GET.get('page', 1)
    tickets = Ticket.gets_by_team_id(
        team.id, limit=TICKETS_COUNT_PER_PAGE,
        start=TICKETS_COUNT_PER_PAGE * (int(page) - 1)) or []
    ticket_total_len = Ticket.get_count_by_team_id(team.id) or 0
    is_closed_tab = False
    n_pages = (ticket_total_len - 1) / TICKETS_COUNT_PER_PAGE + 1
    return HttpResponse(st('/teams/team_pulls.html', **locals()))


def team_pulls_closed(request, name):
    from vilya.models.team import Team
    from vilya.models.ticket import Ticket
    TICKETS_COUNT_PER_PAGE = 30
    team_name = name
    team = Team.get_by_uid(team_name)
    user = request.user
    page = request.GET.get('page', 1)
    tickets = Ticket.gets_by_team_id(
        team.id, closed=True, limit=TICKETS_COUNT_PER_PAGE,
        start=TICKETS_COUNT_PER_PAGE * (int(page) - 1)) or []
    ticket_total_len = Ticket.get_count_by_team_id(team.id,
                                                    closed=True) or 0
    n_pages = (ticket_total_len - 1) / TICKETS_COUNT_PER_PAGE + 1
    is_closed_tab = True
    return HttpResponse(st('/teams/team_pulls.html', **locals()))


def team_issues(request, name):
    from vilya.models.team_issue import TeamIssue
    from vilya.models.team import Team
    from vilya.views.django.project_issue import get_order_type
    from vilya.models.tag import Tag, TAG_TYPE_TEAM_ISSUE
    cls = TeamIssue
    team_uid = name
    team = Team.get_by_uid(team_uid)
    user = request.user
    page = request.GET.get('page', 1)
    state = request.GET.get("state", "open")
    response = HttpResponse()
    order = get_order_type(request, response, 'team_issues_order')

    team_issues = []

    selected_tag_names = request.GET.get('tags', '')
    if selected_tag_names:
        selected_tag_names = selected_tag_names.split(',')
        issue_ids = Tag.get_type_ids_by_names_and_target_id(
            TAG_TYPE_TEAM_ISSUE,
            selected_tag_names,
            team.id)
        team_issues = cls.gets_by_issue_ids(issue_ids, state)
    else:
        team_issues = cls.gets_by_target(team.id, state, order=order)

    n_team_issue = len(team_issues)
    show_tags = team.get_group_tags(selected_tag_names)
    is_closed_tab = None if state == "open" else True
    n_pages = 1
    # TODO: 分页
    response.content = st('issue/team_issues.html', **locals())
    return response


def team_issues_new(request, name):
    from vilya.models.team import Team
    team_uid = name
    team = Team.get_by_uid(team_uid)
    user = request.user
    current_user = request.user
    tags = team.tags
    error = request.GET.get('error')
    teams = Team.get_all_team_uids()
    return HttpResponse(st('issue/new_team_issue.html', **locals()))


@csrf_exempt
def team_issues_create(request, name):
    from dispatches import dispatch
    from vilya.models.team import Team
    from vilya.models.team_issue import TeamIssue
    from vilya.libs.signals import issue_signal
    cls = TeamIssue
    team_uid = name
    team = Team.get_by_uid(team_uid)
    if request.method == 'POST':
        user = request.user
        if not user:
            raise Http404()
        if not team:
            raise Http404()
        title = request.POST.get('title', '').decode('utf-8')
        description = request.POST.get('body', '').decode('utf-8')
        tags = request.POST.get('issue_tags', [])
        if isinstance(tags, list):
            tags = [tag.decode('utf-8') for tag in tags if tag]
        elif isinstance(tags, basestring):
            tags = [tags.decode('utf-8')]

        if not(title and description):
            return HttpResponseRedirect('../new?error=empty')

        tissue = cls.add(title, description, user.name, team=team.id)
        tissue.add_tags(tags, tissue.team_id)
        # TODO: 重构feed后删除这个signal
        issue_signal.send(author=user.name, content=description,
                            issue_id=tissue.issue_id)
        dispatch('issue', data={
            'sender': user.name,
            'content': description,
            'issue': tissue,
        })
        return HttpResponseRedirect(tissue.url)
    return HttpResponseRedirect(team.url + 'issues')
