# -*- coding: utf-8 -*-

import re
from vilya.views.api.utils import jsonize


class GIT2SVNUI(object):
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
        commit = repo.get_commit(part)
        if commit:
            revs = re.findall("trunk@(\w+)", commit.message, re.M)
        return {'git': commit.sha if commit else None,
                'svn': str(revs[0]) if revs else None}
