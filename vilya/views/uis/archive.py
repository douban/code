# -*- coding: utf-8 -*-

from __future__ import absolute_import
from quixote.errors import TraversalError
from vilya.models.project import CodeDoubanProject


class ArchiveUI(object):
    _q_exports = []

    def __init__(self, proj_name):
        project = CodeDoubanProject.get_by_name(proj_name)
        self.project = project

    def _q_lookup(self, request, part):
        repo = self.project.repo
        sha = repo.sha(part)
        if not sha:
            raise TraversalError
        ext = request.get_form_var('ext')
        if ext == 'tar':
            request.response.set_content_type("application/x-tar")
            request.response.set_header("Content-Disposition",
                                        "filename=%s.tar" % part)
            return repo.archive(part, ref=sha, ext=ext)
        elif ext == 'tar.gz':
            request.response.set_content_type("application/x-gzip")
            request.response.set_header("Content-Disposition",
                                        "filename=%s.tar.gz" % part)
            return repo.archive(part, ref=sha)
        request.response.set_content_type("application/x-gzip")
        request.response.set_header("Content-Disposition",
                                    "filename=%s.tar.gz" % part)
        return repo.archive(part, ref=sha)
