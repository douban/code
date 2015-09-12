# -*- coding: utf-8 -*-

import mimetypes
from quixote.errors import TraversalError
from vilya.libs.template import st
from vilya.models.project import CodeDoubanProject
from vilya.models.sphinx_docs import (
    SphinxDocs, guess_builder_from_path)


class SphinxDocsUI:
    _q_exports = []

    def __init__(self, proj_name):
        self.proj = proj_name

    def _q_access(self, request):
        self.docs = SphinxDocs(self.proj)
        if not self.docs.enabled:
            raise TraversalError(
                "docs not enabled: %s" % self.docs.disabled_reason)
        self.builder_name, self.explicit_builder = guess_builder_from_path(
            self.docs.builders, self.proj, request.get_path())
        if self.explicit_builder:
            self.base_path = "/%s/docs/%s/" % (self.proj, self.builder_name)
        else:
            self.base_path = "/%s/docs/" % (self.proj)
        self.builder = self.docs.get_builder(self.builder_name)
        if not self.builder:
            raise TraversalError("Unknown builder")

    def _q_index(self, request):
        return self.get_content(request, '')

    def get_content(self, request, path):
        tdt = _tmpl_common_data(None, path, self.proj, request)
        if not self.builder.has_content():
            tdt['docsdir'] = self.builder.dir
            return st('sphinx_docs_start.html', **tdt)
        if path in self.builder.redirects:
            return request.redirect("%s%s" % (
                self.base_path, self.builder.redirects[path]))
        if self.builder.file_is_static(path):
            # Serve static files, cannot use nginx rerouting because
            # code permdir is not on MFS
            content = self.builder.file_content(path)
            if content is False:
                raise TraversalError(
                    "Static content not found in %s" % path)
            ct = mimetypes.guess_type(path)
            request.response.set_content_type(
                ct[0] if ct else 'application/octet-stream')
            return content
        fvars = dict((_, request.get_form_var(
            _)) for _ in self.builder.needed_form_vars)
        if self.builder.template:
            tdt['doc'] = {
                'with_comment': self.builder.with_comment(),
                'docsdir': self.builder.dir,
                'base_path': self.base_path,
            }
            tdt['doc'].update(self.builder.template_data(path, fvars))
            return st(self.builder.template, **tdt)
        else:
            content = self.builder.raw_content(path, fvars)
            if content is False:
                raise TraversalError(
                    "Builder %s did not find content file for %s" % (
                        self.builder_name, path))
            return content

    def _q_lookup(self, request, piece):
        if self.explicit_builder:
            assert piece == self.builder_name, \
                "Explicit builder means it is in url: proj/docs/builder_name/..."  # noqa
            piece = ''
        if self.builder.slash_urls:
            return DocsRecursorUI(self.proj, piece, self.get_content)
        else:
            return DocsRecursorUICallable(self.proj, piece, self.get_content)


def debug_tdt(tdt, path):
    from pprint import pprint
    print "DISPLAYING PICKLED DATA FOR PATH:", path
    for k in tdt:
        print
        print k
        print "====="
        if k == 'gc':
            pprint(tdt[k])
        else:
            print tdt[k]


def _tmpl_common_data(rev, path, project_name, request):
    project = CodeDoubanProject.get_by_name(project_name)
    user = request.user
    ref = rev
    if ref is None:
        ref = project.default_branch
    branches = project.repo.branches
    tags = project.repo.tags
    ref_type = 'branch' if ref in branches else 'tag' \
               if ref in tags else 'tree'
    blob_path = path.decode('utf-8')
    tdt = {
        'errors': '',
        'branches': branches,
        'rev': rev,
        'tags': tags,
        'blob_path': blob_path,
        'file_name': blob_path.rpartition('/')[-1],
        'request': request,
        'project': project,
        'project_name': project_name,
        'path': path,
        'ref_type': ref_type,
        'blob_ref': ref,
        'ref': ref,
        'user': user,
    }
    return tdt


class DocsRecursorUI(object):
    _q_exports = []

    def __init__(self, proj, piece, get_content):
        if piece:
            self.parts = [piece]
        else:
            self.parts = []
        self.proj = proj
        self.get_content = get_content

    def _q_lookup(self, request, part):
        self.parts.append(part)
        return self

    def _q_index(self, request):
        return self.get_content(request, '/'.join(self.parts))


class DocsRecursorUICallable(DocsRecursorUI):
    def __call__(self, request):
        return self.get_content(request, '/'.join(self.parts))
