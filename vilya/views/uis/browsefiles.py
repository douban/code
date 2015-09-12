# -*- coding: utf-8 -*-

from __future__ import absolute_import

import json
from vilya.libs.template import st
from vilya.models.project import CodeDoubanProject

_q_exports = []


class BrowsefilesUI:
    _q_exports = ['setting']

    def __init__(self, proj_name):
        self.proj = proj_name

    def _q_access(self, request):
        if 'json' in request.environ['HTTP_ACCEPT']:
            self.output = 'json'
        else:
            self.output = 'html'

    def _q_index(self, request):
        project = CodeDoubanProject.get_by_name(self.proj)
        user = request.user
        path = request.get_form_var('path', '')
        rev = request.get_form_var('rev', project.default_branch)
        allfiles = project.repo.get_tree(rev, path=path)
        allfiles = [_add_file_type_and_warns(f) for f in allfiles]
        errors = ''
        project_name = self.proj
        project = CodeDoubanProject.get_by_name(project_name)
        ref = rev
        if ref is None:
            ref = project.default_branch
        branches = project.repo.branches
        tags = project.repo.tags
        ref_type = 'branch' if ref in branches else 'tag' \
                   if ref in tags else 'tree'
        if self.output == 'json':
            return json.dumps(allfiles)
        else:
            return st('browsefiles.html', **locals())


def _add_file_type_and_warns(node):
    code_file_exts = 'py rb c h html mako ptl js css less handlebars coffee sql'.split()  # noqa
    bad_exts = 'pyc exe'.split()
    node_ext = node['path'].rsplit('.')[1] if '.' in node['path'] else ''
    if node['type'] == 'tree':
        icon_type = 'directory'
    elif node['type'] == 'commit':
        icon_type = 'submodule'
    elif node_ext in code_file_exts:
        icon_type = 'code-file'
    else:
        icon_type = 'text-file'
    node['icon-type'] = icon_type
    if node_ext in bad_exts:
        node['warn'] = 'bad'
    else:
        node['warn'] = 'no'
    return node
