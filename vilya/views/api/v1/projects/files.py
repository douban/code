# -*- coding: utf-8 -*-

from __future__ import absolute_import
from vilya.views.api.utils import RestAPIUI


class FilesUI(RestAPIUI):
    _q_exports = []
    _q_methods = ['get']

    def __init__(self, project):
        self.project = project

    def get(self, request):
        path = request.get_form_var('path', '')
        rev = request.get_form_var('rev', 'HEAD')
        repo = self.project.repo
        files = repo.get_tree(rev, path=path)
        return [f for f in files]


class FileUI(RestAPIUI):
    _q_exports = []
    _q_methods = ['get']

    def __init__(self, project):
        self.project = project

    def get(self, request):
        path = request.get_form_var('path', '')
        rev = request.get_form_var('rev', 'HEAD')
        content = render_file(self.project, rev, path)
        data = {'path': path,
                'type': 'blob',
                'content': content}
        return data


def render_file(project, rev, path):
    from vilya.libs.text import highlight_code, format_md_or_rst
    ref = ':'.join((rev, path))
    content = '<div class="error"><i class="icon-exclamation-sign"></i> File not found.</div>'
    try:
        blob = project.repo.get_path_by_ref(ref)
        if blob and blob.type == 'blob':
            if blob.binary:
                if path.endswith('.pdf'):
                    content = '<a class="media" href="%s"></a>' % str('/' + project.name + '/raw/' + rev + '/' + path)
                else:
                    content = '<div class="rawfile">The content of %s appear to be raw binary, please use raw view instead</div>' % path
            elif path.endswith(('md', 'mkd', 'markdown')):
                content = '<div class="markdown-body">%s</div>' % format_md_or_rst(path, blob.data)
            else:
                content = highlight_code(path, blob.data, div=True)
    except (KeyError, ValueError):
        pass
    return content
