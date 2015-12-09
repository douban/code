# -*- coding: utf-8 -*-

from quixote.errors import TraversalError
from vilya.views.util import jsonize, render_actions
from vilya.models.feed import get_public_feed, get_user_feed, get_user_inbox, PAGE_ACTIONS_COUNT

_q_exports = ['pub', 'notify', 'team', 'userfeed']

class PubUI(object):
    _q_exports = []

    @jsonize
    def _q_lookup(self, request, num):
        if not num.isdigit():
            raise TraversalError
        num = int(num)
        actions = get_public_feed().get_actions(start=num, stop=num+PAGE_ACTIONS_COUNT-1)
        length = len(actions)
        render_html = render_actions(actions, show_avatar=True)
        return {'result': render_html, 'length': length}


class FeedUI(object):
    _q_exports = []

    @jsonize
    def _q_lookup(self, request, num):
        user = request.user
        if not user or not num.isdigit():
            raise TraversalError
        num = int(num)
        actions = get_user_inbox(user.username).get_actions(start=num, stop=num+PAGE_ACTIONS_COUNT-1)
        length = len(actions)
        render_html = render_actions(actions, show_avatar=True)

        return {'result': render_html, 'length': length}


class NotifyUI(object):
    _q_exports = []

    @jsonize
    def _q_lookup(self, request, num):
        if not num.isdigit():
            raise TraversalError
        return {'r': 1}



pub = PubUI()
userfeed = FeedUI()
notify = NotifyUI()
