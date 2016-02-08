# -*- coding: utf-8 -*-

from django.http import HttpResponse
from vilya.libs.template import st


def index(request):
    return HttpResponse("Hello, world. You're at the vilya index.")


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
