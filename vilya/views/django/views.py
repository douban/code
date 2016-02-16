# -*- coding: utf-8 -*-

import json
from django.http import Http404
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from vilya.libs.template import st


def mirrors(request):
    from vilya.models.project import CodeDoubanProject
    your_projects = CodeDoubanProject.get_projects(
        owner="mirror", sortby='sumup')
    return HttpResponse(st('/mirrors.html', **locals()))


def m_index(request):
    return HttpResponse(st('/m/feed.html', **locals()))


def m_public_timeline(request):
    is_public = True
    return HttpResponse(st('/m/feed.html', **locals()))


def m_actions(request):
    from vilya.models.feed import get_user_inbox, get_public_feed
    MAX_ACT_COUNT = 100

    since_id = request.GET.get('since_id', '')
    is_public = request.GET.get('is_public', '')
    user = request.user
    all_actions = []
    if is_public == 'true':
        all_actions = get_public_feed().get_actions(0, MAX_ACT_COUNT)
    elif user:
        all_actions = get_user_inbox(user.username).get_actions(
            0, MAX_ACT_COUNT)
    if since_id:
        actions = []
        for action in all_actions:
            if action.get('uid') == since_id:
                break
            actions.append(action)
    else:
        actions = all_actions
    return HttpResponse(st('/m/actions.html', **locals()))


@csrf_exempt
def j_pull_edit(request, id):
    from vilya.models.ticket import Ticket
    from vilya.models.project import CodeDoubanProject
    from vilya.models.pull import PullRequest
    from vilya.libs.text import parse_emoji, render_markdown_with_project
    ticket = Ticket.get(id)
    if not ticket:
        raise Http404()

    ticket_id = ticket.ticket_number
    project = CodeDoubanProject.get(ticket.project_id)
    pullreq = PullRequest.get_by_proj_and_ticket(project.id, ticket_id)
    proj_name = project.name
    if request.method == 'POST':
        title = request.POST.get('title', '').decode('utf-8')
        content = request.POST.get('content', '').decode('utf-8')
        user = request.user
        user = user.name if user else None
        if user == ticket.author:
            ticket.update(title, content)
            content_html = render_markdown_with_project(
                content, proj_name)
            content_html += st('/widgets/markdown_checklist.html',
                                **locals())
            return HttpResponse(json.dumps({'r': 0,
                                            'title': title,
                                            'content': content,
                                            'title_html': parse_emoji(title),
                                            'content_html': content_html}))
    return HttpResponse(json.dumps({'r': 1}))


@csrf_exempt
def j_issue_edit(request, id):
    from vilya.libs.text import (
        parse_emoji,
        render_markdown_with_project,
        render_markdown
    )
    from vilya.models.issue import Issue
    issue = Issue.get_cached_issue(id)
    if not issue:
        raise Http404()

    if request.method == 'POST':
        title = request.POST.get('title', '').decode('utf-8')
        if not title.strip():
            return HttpResponse(json.dumps({'r': 1}))
        content = request.POST.get('content', '').decode('utf-8')
        user = request.user
        user = user.name if user else None
        if issue and user == issue.creator_id:
            issue.update(title, content)
            if issue == "project":
                content_html = render_markdown_with_project(
                    content, issue.target.name)
            else:
                content_html = render_markdown(content)
            content_html += st('/widgets/markdown_checklist.html',
                                **locals())
            return HttpResponse(json.dumps({'r': 0,
                    'title': title,
                    'content': content,
                    'title_html': parse_emoji(title),
                    'content_html': content_html}))
    return HttpResponse(json.dumps({'r': 1}))


@csrf_exempt
def j_issue_delete_tag(request):
    from vilya.views.models.tag import (
        TagName,
        Tag,
        TAG_TYPE_PROJECT_ISSUE,
        TAG_TYPE_TEAM_ISSUE
    )
    from vilya.views.models.project import CodeDoubanProject
    from vilya.views.models.team import Team
    # FIXME: ugly
    if request.method == "POST":
        user = request.user
        if not user:
            return HttpResponse(json.dumps({'r': 0, 'msg': '未登录，请先登录'}))
        tag_name = request.POST.get('tag_name', '').decode('utf-8')
        tag_type = request.POST.get('tag_type', '')
        tag_target_id = request.POST.get('tag_target_id', '')

        if not tag_name:
            return HttpResponse(json.dumps({'r': 0, 'msg': 'tag不能为空'}))
        try:
            tag_type, tag_target_id = int(tag_type), int(tag_target_id)
        except:
            return HttpResponse(json.dumps({'r': 0, 'msg': '错误的数据类型'}))

        if tag_type == TAG_TYPE_PROJECT_ISSUE:
            target = CodeDoubanProject.get(tag_target_id)
        elif tag_type == TAG_TYPE_TEAM_ISSUE:
            target = Team.get(tag_target_id)
        else:
            return HttpResponse(json.dumps({'r': 0, 'msg': '错误的数据类型'}))

        if not target.is_admin(user.name):
            return HttpResponse(json.dumps({'r': 0, 'msg': '没有操作权限'}))

        tname = TagName.get_by_name_and_target_id(
            tag_name, tag_type, target.id)
        if not tname:
            return HttpResponse(json.dumps({'r': 0, 'msg': 'tag不存在'}))

        tags = Tag.gets_by_tag_id(tname.id)
        for tag in tags:
            tag.delete()
        tname.delete()
        return HttpResponse(json.dumps({'r': 1, 'msg': '删除成功'}))


@csrf_exempt
def j_chat_delete_room(request):
    from vilya.models.room import Room
    from vilya.models.message import get_room_message
    room_name = request.POST.get('room_name', '')
    if Room.delete(room_name):
        get_room_message(room_name).delete_by_key()
        return HttpResponse(json.dumps({'r': 1, 'msg': '删除成功'}))
    return HttpResponse(json.dumps({'r': 0, 'msg': '删除失败, 可能该room已被删除'}))


@csrf_exempt
def j_chat_room(request, name):
    from datetime import datetime
    from vilya.models.message import get_room_message
    from vilya.views.util import render_message
    from vilya.models.room import Room
    room_name = name
    if request.method == "POST":
        content = request.POST.get('message')
        author = request.user.username
        date = datetime.now()
        message_data = {
            "content": content,
            "author": author,
            "date": date
        }
        room_message = get_room_message(room_name)
        room_message.add_message(message_data)
        return HttpResponse(json.dumps({'r': 1}))
    if request.method == "GET":
        if room_name != 'lobby' and not Room.exists(room_name):
            return HttpResponse(json.dumps({'r': 0, 'msg': 'room not exists'}))
        room_message = get_room_message(room_name)
        messages = room_message.get_messages()
        render_messages = [render_message(m) for m in messages]
        return HttpResponse(json.dumps({'r': 1, 'msg': render_messages}))


@csrf_exempt
def j_fav(request):
    from vilya.models.user_fav import UserFavItem
    from vilya.models.consts import K_PULL, K_ISSUE
    user = request.user
    tid = request.POST.get('tid', '')
    tkind = request.POST.get('tkind', '0')
    tkind = int(tkind)
    if not user or tkind not in [K_PULL, K_ISSUE]:
        return HttpResponse(json.dumps({'r': 1}))
    if request.method == "POST":
        UserFavItem.add(user.username, tid, tkind)
    elif request.method == 'DELETE':
        UserFavItem.delete_by_user_target_kind(user.username, tid, tkind)
    else:
        return HttpResponse(json.dumps({'r': 1}))
    return HttpResponse(json.dumps({'r': 0}))


@csrf_exempt
def j_hooks_telchar(request, id):
    from vilya.models.project import CodeDoubanProject
    from vilya.models.hook import CodeDoubanHook
    from vilya.models.consts import TELCHAR_URL
    user = request.user
    project = CodeDoubanProject.get(id)
    url = TELCHAR_URL

    if project.is_owner(user):
        is_disable = request.POST.get('close', '')
        if is_disable:
            hook = CodeDoubanHook.get_by_url(url)
            if hook:
                hook.destroy()
            status = 0
        else:
            CodeDoubanHook.add(url, id)
            status = 1
        return HttpResponse(json.dumps({'r': 0, 'status': status}))
    return HttpResponse(json.dumps({'r': 1}))


def j_more_pub(request, id):
    from vilya.models.feed import get_public_feed, PAGE_ACTIONS_COUNT
    from vilya.views.util import render_actions
    num = int(id)
    actions = get_public_feed().get_actions(start=num, stop=num+PAGE_ACTIONS_COUNT-1)
    length = len(actions)
    render_html = render_actions(actions, show_avatar=True)
    return HttpResponse(json.dumps({'result': render_html, 'length': length}))


def j_more_userfeed(request, number):
    from vilya.models.feed import get_user_inbox, PAGE_ACTIONS_COUNT
    from vilya.views.util import render_actions
    user = request.user
    if not user or not number.isdigit():
        raise Http404()
    num = int(number)
    actions = get_user_inbox(user.username).get_actions(start=num, stop=num+PAGE_ACTIONS_COUNT-1)
    length = len(actions)
    render_html = render_actions(actions, show_avatar=True)
    return HttpResponse(json.dumps({'result': render_html, 'length': length}))


def j_more_notify(request, id):
    return HttpResponse(json.dumps({'r': 1}))


def j_more_team(request, name, number):
    from vilya.models.feed import get_team_feed, PAGE_ACTIONS_COUNT
    from vilya.models.team import Team
    from vilya.views.util import render_actions
    num = int(number)
    team = Team.get_by_uid(name)
    actions = get_team_feed(team.id).get_actions(start=num,
                                                 stop=num+PAGE_ACTIONS_COUNT-1)
    length = len(actions)
    render_html = render_actions(actions, show_avatar=True)
    return HttpResponse(json.dumps({'result': render_html, 'length': length}))
