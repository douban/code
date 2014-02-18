# -*- coding: utf-8 -*-

from __future__ import absolute_import
from vilya.views.api import errors
from vilya.views.api.utils import RestAPIUI


class ContentsUI(RestAPIUI):
    _q_exports = []

    def __init__(self, project):
        self.project = project

    def _q_lookup(self, request, part):
        return ContentUI(self.project, part)


class ContentUI(RestAPIUI):
    _q_exports = []
    _q_methods = ['get']

    def __init__(self, project, path):
        self.project = project
        self.paths = [path]

    def get(self, request):
        repo = self.project.repo
        path = '/'.join(self.paths)
        ref = request.get_form_var("ref", "HEAD")
        item = repo.get_path_by_ref("%s:%s" % (ref, path))
        if not item:
            raise errors.NotFoundError('blob %s', path)
        if item.type != "blob":
            raise errors.NotFoundError('blob %s', path)
        commit = repo.get_last_commit(ref, path=path)
        r = item.as_dict()
        r['last_commit'] = commit.as_dict()
        return r

    def _q_lookup(self, request, part):
        self.paths.append(part)
        return self
