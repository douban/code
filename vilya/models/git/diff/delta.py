# -*- coding: utf-8 -*-

from __future__ import absolute_import


class Delta(object):
    '''Brief Diff'''

    def __init__(self, repo, diff, patch):
        self.repo = repo
        self.diff = diff
        self._patch = patch
        self.old_sha = patch['old_sha']
        self.new_sha = patch['new_sha']
        self.old_file_sha = patch['old_oid']
        self.new_file_sha = patch['new_oid']
        self.status = patch['status']
        self.old_file_path = patch['old_file_path']
        self.new_file_path = patch['new_file_path']
        self.binary = patch['binary']

    @property
    def status_text(self):
        status = self.status
        if status == 'A':
            return 'added'
        elif status == 'D':
            return 'deleted'
        elif status == 'M':
            return 'modified'
        elif status == 'C':
            return 'added'
        elif status == 'R':
            return 'renamed'
        return 'modified'


