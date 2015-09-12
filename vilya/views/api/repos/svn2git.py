# -*- coding: utf-8 -*-

import re
from vilya.views.api.utils import jsonize


class SVN2GITUI(object):
    _q_exports = []

    def __init__(self, repo):
        self.repo = repo

    @jsonize
    def _q_index(self, request):
        return {}

    @jsonize
    def _q_lookup(self, request, part):
        if self.repo.name not in ['shire_git_RO',
                                  'shire',
                                  'testuser/test']:
            return {}
        repo = self.repo.repo
        query = 'trunk@' if part == 'HEAD' else "trunk@%s " % part
        commits = repo.get_commits("HEAD",
                                   query=query,
                                   max_count=1)
        commit = commits[0] if commits else None
        if commit and part == 'HEAD':
            revs = re.findall("trunk@(\w+)", commit.message, re.M)
            part = str(revs[0]) if revs else None
        return {'git': commit.sha if commit else None,
                'svn': part}
