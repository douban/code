# -*- coding: utf-8 -*-
from vilya.models.gist import Gist, gist_detail
from vilya.libs.text import highlight_code, format_md_or_rst
from vilya.libs import api_errors
from vilya.views.api.comments import GistCommentsUI
from vilya.views.api.utils import http_status, jsonize, RestAPIUI

_q_exports = []


def _q_lookup(request, id):
    return GistUI(request, id)


class GistUI(RestAPIUI):

    _q_exports = ['src', 'source', 'star', 'forks', 'comments']
    _q_methods = ['get', 'patch', 'delete']

    def __init__(self, request, id):
        self.id = id
        self.gist = Gist.get(self.id)

        if not self.gist:
            raise api_errors.NotFoundError("gist")

        self.is_owner = False
        self.comments = GistCommentsUI(request, self.gist)

    def _q_access(self, req):
        if not req.get_path().endswith(('/', 'src', 'source')) \
           and not req.user:
            raise api_errors.UnauthorizedError

        if req.user and req.user.username == self.gist.owner_id:
            self.is_owner = True

    def get(self, request):
        if not (self.gist.is_public or self.is_owner):
            raise api_errors.ForbiddenError
        ret = gist_detail(self.gist, include_forks=True)
        return ret

    def delete(self, request):
        if not self.is_owner:
            raise api_errors.NotTheAuthorError('gist', 'delete')

        self.gist.delete()

    def patch(self, request):
        if not self.is_owner:
            raise api_errors.NotTheAuthorError('gist', 'update')

        desc = request.data.get('description')
        if not desc:
            desc = self.gist.description

        files = request.data.get('files')
        file_names = []
        file_contents = []

        for file_name in self.gist.files:
            if file_name in files:
                file = files[file_name]
                if file:
                    file_names.append(file_name)
                    file_contents.append(file.get("content"))
            else:
                file_names.append(file_name)
                file_contents.append(self.gist.get_file(file_name))

        self.gist.update(desc, file_names, file_contents)
        gist = Gist.get(self.gist.id)
        return gist_detail(gist, include_forks=True)

    @jsonize
    @http_status(204)
    def star(self, request):
        method = request.method
        user_id = request.user.username
        if method == 'PUT':
            self.gist.star(user_id)
        elif method == 'DELETE':
            self.gist.unstar(user_id)
        elif method == 'GET':
            if not self.gist.is_starred(user_id):
                request.response.set_status(404)

    @jsonize
    @http_status(201)
    def forks(self, request):
        if request.method == 'POST':
            gist = self.gist.fork(request.user.username)
            ret = gist_detail(gist, include_forks=True)
            return ret

    @jsonize
    def src(self, request):
        path = request.get_form_var('path', '')
        ref = request.get_form_var('ref', 'HEAD')
        item = self.gist.repo.get_path(ref, path)
        t = 'blob' if not item else item.type
        if item and t == 'blob':
            src = item.data
            src = self._render_src(path, src)
        elif t == 'tree':
            src = [dict(e) for e in item]
        else:
            src = '<div class="error"><i class="icon-exclamation-sign"></i> File not found.</div>'  # noqa
        data = {'path': path, 'type': t, 'src': src}
        return data

    def _render_src(self, path, src):
        if path.endswith(('md', 'mkd', 'markdown')):
            return '<div class="markdown-body">%s</div>' % format_md_or_rst(
                path, src)
        return highlight_code(path, src)

    @jsonize
    def source(self, request):
        path = request.get_form_var('path', '')
        ref = request.get_form_var('ref', 'HEAD')
        item = self.gist.repo.get_path(ref, path)
        t = 'blob' if not item else item.type
        if item and t == 'blob':
            src = item.data
        elif t == 'tree':
            src = [dict(e) for e in item]
        else:
            src = '<div class="error"><i class="icon-exclamation-sign"></i> File not found.</div>'  # noqa
        return dict(path=path, source=src)
