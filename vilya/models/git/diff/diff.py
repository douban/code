# -*- coding: utf-8 -*-

from __future__ import absolute_import
from itertools import groupby
from vilya.models.utils.decorators import cached_property
from vilya.models.git.diff.patch import Patch
from vilya.models.git.diff.delta import Delta


class Diff(object):

    def __init__(self, repo, diff, linecomments=[]):
        self.repo = repo
        self.raw_diff = diff
        self.old_ref = None
        self.new_ref = None
        self.old_sha = diff['old_sha']
        self.new_sha = diff['new_sha']
        self._additions = 0
        self._deletions = 0
        self._length = 0

        # 实例化 Patches
        # line comments groupby path
        keyfunc_path = lambda x: x.old_path
        linecomments_by_path = {}
        if linecomments:
            linecomments.sort(key=keyfunc_path)
            linecomments_by_path = dict(
                (k, list(v)) for k, v in groupby(linecomments,
                                                 key=keyfunc_path))
        self._linecomments_by_path = linecomments_by_path

        # TODO: MAX_DIFF_PATCHES

    @property
    def additions(self):
        if self._additions:
            return self._additions
        for p in self.patches:
            self._additions += p.additions
        return self._additions

    @property
    def deletions(self):
        if self._deletions:
            return self._deletions
        for p in self.patches:
            self._deletions += p.deletions
        return self._deletions

    @property
    def length(self):
        if self._length:
            return self._length
        self._length = len(self.patches)
        return self._length

    @cached_property
    def deltas(self):
        repo = self.repo
        diff = self.raw_diff
        return [Delta(repo, self, p)
                for p in diff['patches']]

    @cached_property
    def patches(self):
        repo = self.repo
        diff = self.raw_diff
        linecomments_by_path = self._linecomments_by_path
        # TODO: use generator
        return [Patch(repo, self, p, linecomments_by_path.get(p['old_file_path'], []))
                for p in diff['patches']]
