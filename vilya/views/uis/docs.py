# -*- coding: utf-8 -*-
from __future__ import absolute_import
from quixote.errors import TraversalError
from vilya.libs.template import st
from vilya.models.doc import (
    get_doc_builder, doc_exists, PickleDoc, HTMLDoc)


class DocsUI(object):
    _q_exports = []

    def __init__(self, project):
        self.project = project
        self.project_conf = project.conf
        self.conf = self.project_conf.get('docs')

    def _q_access(self, request):
        # check doc exist
        if not self.conf:
            raise TraversalError

    def _q_index(self, request):
        # docs index
        return ''

    def _q_lookup(self, request, part):
        # check doc type: html or pickle
        if part not in self.conf:
            raise TraversalError
        if not doc_exists(self.project):
            raise TraversalError
        doc = self.conf.get(part)
        builder = get_doc_builder(doc, part)
        if not builder:
            raise TraversalError
        if builder == 'pickle':
            # pickle
            return DocUI(PickleDoc, self.project, part)
        elif builder == 'html':
            # html
            return DocUI(HTMLDoc, self.project, part)
        else:
            # raw
            return DocUI(HTMLDoc, self.project, part)
        raise TraversalError


class DocUI(object):
    _q_exports = []

    def __init__(self, doc, project, id):
        self.doc = doc  # Doc class
        self.project = project
        self.id = id  # Doc unique name
        self.parts = []

    def _q_index(self, request):
        user = request.user
        path = '/'.join(self.parts)
        doc = self.doc(self.project, self.id, path)
        if not doc.exists:
            raise TraversalError
        if doc.is_template:
            tdt = {
                'errors': '',
                'user': user,
                'request': request,
                'project': self.project,
            }
            # FIXME
            tdt['doc'] = {
            #    'with_comment': self.builder.with_comment(),
            #    'docsdir': self.builder.dir,
            #    'base_path': self.base_path,
                'docsdir': '',
                'base_path': '',
            }
            tdt['doc'].update(doc.content)
            return st(doc.template, **tdt)
        request.response.set_content_type(doc.content_type)
        return doc.content

    def __call__(self, request):
        return self._q_index(request)

    def _q_lookup(self, request, part):
        self.parts.append(part)
        return self
