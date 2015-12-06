# -*- coding: utf-8 -*-

import re
import json

from quixote.errors import TraversalError

from vilya.models.commit_statuses import CommitStatuses
from dispatches import dispatch


class StatusesUI:
    _q_exports = []

    def __init__(self, request, project):
        self.project = project

    def __call__(self, request):
        return self._index(request)

    def _q_index(self, request):
        return self._index(request)

    def _index(self, request):
        return 'Hello'

    def _push_qaci_noti(self, sha, state, target_url):
        project = self.project
        pulls = project.open_family_pulls
        for p in pulls:
            if sha in p.get_commits_shas() and state in ('success',
                                                         'failure'):
                dispatch('qaci', data=dict(sha=sha,
                                           pull=p,
                                           project=project,
                                           state=state,
                                           url=target_url))

    def _add_status(self, request, sha):
        cs = CommitStatuses(self.project.id, sha)
        state = request.get_form_var('state')
        target_url = request.get_form_var('target_url')
        description = request.get_form_var('description')
        s = cs.add(state, target_url, description, 'qaci')
        self._push_qaci_noti(sha, state, target_url)
        request.response.set_status(201)
        return json.dumps(s.as_dict())

    def _q_lookup(self, request, sha):
        if request.method == 'POST':
            return self._add_status(request, sha)

        cs = CommitStatuses(self.project.id, sha)
        if re.match(r'^\d+$', sha):
            # using id got one
            s = cs.get(sha)
            if s:
                return json.dumps(s.as_dict())
            else:
                raise TraversalError()

        else:
            statuses = cs.all()
            statuses = [s.as_dict() for s in statuses]
            return json.dumps(statuses)
