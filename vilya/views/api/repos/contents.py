# -*- coding: utf-8 -*-

from vilya.libs import api_errors
from vilya.views.api.utils import RestAPIUI


class ContentsUI(RestAPIUI):
    _q_exports = []

    def __init__(self, repo):
        self.repo = repo

    def _q_lookup(self, request, part):
        return ContentUI(self.repo, part)


class ContentUI(RestAPIUI):
    _q_exports = []
    _q_methods = ['get']

    def __init__(self, repo, path):
        self.repo = repo
        self.path = path

    def get(self, request):
        repo = self.repo.repo
        path = self.path
        ref = request.get_form_var("ref", "HEAD")
        item = repo.get_path_by_ref("%s:%s" % (ref, path))
        if not item:
            raise api_errors.NotFoundError('blob %s', path)
        if item.type != "blob":
            raise api_errors.NotFoundError('blob %s', path)
        commit = repo.get_last_commit(ref, path=path)
        r = item.as_dict()
        r['last_commit'] = commit.as_dict()
        return r
