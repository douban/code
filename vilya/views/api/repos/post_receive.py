# -*- coding: utf-8 -*-

import json
from dispatches import dispatch
from vilya.models.hooks.events.push import PushPayload


class PostReceiveUI(object):
    _q_exports = []

    def __init__(self, repo):
        self.repo = repo

    def _q_index(self, request):
        if request.method != "POST":
            return json.dumps({'r': 0})
        data = request.get_form_var('payload')
        if not data:
            return json.dumps({'r': 0})
        data = json.loads(data)
        for ref in data.get('refs', []):
            push = PushPayload(
                self.repo, ref.get('old_value'), ref.get('new_value'),
                ref.get('ref_name'), ref.get('user_name'))
            dispatch('push_actions', data=push.payload)
        return json.dumps({'r': 1})
