# -*- coding: utf-8 -*-

from __future__ import absolute_import

from vilya.libs.template import st
from vilya.models.feed import get_user_inbox, get_public_feed

MAX_ACT_COUNT = 100


_q_exports = ['actions', 'public_timeline']


def _q_index(request):
    return st('/m/feed.html', **locals())


def public_timeline(request):
    is_public = True
    return st('/m/feed.html', **locals())


def actions(request):
    since_id = request.get_form_var('since_id', '')
    is_public = request.get_form_var('is_public', '')
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
    return st('/m/actions.html', **locals())
