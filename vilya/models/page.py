# -*- coding: utf-8 -*-

from __future__ import absolute_import
import mimetypes


class Page(object):

    def __init__(self, project, path):
        self.project = project
        self.path = path
        self._content = self.get_file(path)

    def get_file(self, path):
        # FIXME: default branch?
        blob = self.project.repo.get_file('master', path)
        if blob:
            return blob.data

    @property
    def exist(self):
        if self._content is not None:
            return True
        return False

    @property
    def content(self):
        return self._content

    @property
    def content_type(self):
        ct = mimetypes.guess_type(self.path)
        if ct:
            return ct[0]
        return 'application/octet-stream'

