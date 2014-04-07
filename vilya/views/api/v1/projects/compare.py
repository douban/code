# -*- coding: utf-8 -*-

from __future__ import absolute_import
import json
from vilya.views.api.utils import RestAPIUI


class CompareUI(RestAPIUI):
    _q_exports = []
    _q_methods = ['get']

    def __init__(self, project):
        self.project = project

    def get(self, request):
        sha1 = request.get_form_var('sha1')
        sha2 = request.get_form_var('sha2')
        data = {}
        if sha1 and sha2:
            data = compare_commit(self.project, sha1, sha2)
        return data

    def _q_lookup(self, request, part):
        data = {}
        try:
            sha1, sha2 = part.split('...')
            if sha1 and sha2:
                data = compare_commit(self.project, sha1, sha2)
        except ValueError:
            pass
        return json.dumps(data)


def compare_commit(project, sha1, sha2):
    data = {}
    commits = project.repo.get_commits(sha2, sha1)
    diff = project.repo.get_diff(sha2,
                                 from_ref=sha1,
                                 rename_detection=True)
    data['old_sha'] = sha1
    data['new_sha'] = sha2
    data['commits'] = [c.as_dict() for c in commits]
    raw_diff = diff.raw_diff
    try:
        del raw_diff['diff']
    except KeyError:
        pass
    data['diff'] = raw_diff
    return data
