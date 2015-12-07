# -*- coding: utf-8 -*-

import json
import inspect
from quixote.errors import TraversalError
from quixote.errors import AccessError

from vilya.libs.template import st, request
from vilya.models.user import User
from vilya.models.gist import Gist
from vilya.models.gist_star import GistStar
from vilya.models.gist_comment import GistComment
from vilya.libs.text import highlight_code
from vilya.views.util import is_mobile_device
from vilya.config import DOMAIN
from tasks import index_a_gist

_q_exports = ['discover', 'forked', 'starred']


def _q_index(request):
    user = request.user
    if request.method == 'POST':
        desc, is_public, names, contents, oids = _get_req_gist_data(request)
        user = request.user
        owner_id = user and user.username or Gist.ANONYMOUS
        gist = Gist.add(desc, owner_id, is_public, names, contents)
        return request.redirect(gist.url)

    tdt = dict(request=request, gists=[], user=user)
    if user:
        gists = Gist.gets_by_owner(user.username, limit=4)
        tdt.update(dict(gists=gists))

    if is_mobile_device(request):
        return st('/m/gist/index.html', **tdt)
    return st('/gist/index.html', **tdt)


def _discover(request):
    user = request.user
    name = inspect.stack()[1][3]
    (page, start, link_prev, link_next, sort,
     direction) = make_page_args(request, name)
    gists = Gist.discover(name, sort, direction, start)
    tdt = dict(
        request=request,
        gists=gists,
        page=page,
        link_prev=link_prev,
        link_next=link_next,
        sort=sort,
        direction=direction,
        user=user
    )
    return st('/gist/gists.html', **tdt)


def discover(request):
    return _discover(request)


def forked(request):
    return _discover(request)


def starred(request):
    return _discover(request)


def _q_lookup(request, item):
    if item.isdigit():
        return GistUI(item)

    if item.count('.') == 1:
        gid, extend = item.split('.')
        if extend == 'js' and gid.isdigit():
            return GistEmbedUI(gid)

    return UserGistUI(item)


class GistUI:
    _q_exports = ['revisions', 'forks', 'stars', 'fork', 'star', 'unstar',
                  'edit', 'delete', 'comments', 'download', 're_index']

    @property
    def comments(self):
        return GistCommentUI(self.id)

    def __init__(self, id):
        self.id = id
        self.gist = Gist.get(id)

    def _q_index(self, request):
        user = request.user
        tdt = dict(request=request, gist=self.gist, ref='master', user=user)
        if is_mobile_device(request):
            return st('/m/gist/gist_detail.html', **tdt)
        return st('/gist/gist_detail.html', **tdt)

    def _q_lookup(self, request, sha1):
        user = request.user
        if sha1 == 'raw':
            return RawGistUI(self.id)
        if sha1 is None or not self.gist.repo.is_commit(sha1):
            return TraversalError()
        tdt = {'request': request,
               'gist': self.gist,
               'ref': sha1,
               'user': user}
        return st('/gist/gist_detail.html', **tdt)

    def edit(self, request):
        gist = self.gist
        user = request.user
        if not user or user.username != gist.owner_id:
            raise AccessError()
        if request.method == 'POST':
            desc, is_public, names, contents, oids = _get_req_gist_data(
                request)
            gist.update(desc, names, contents, oids)
            return request.redirect(gist.url)
        tdt = dict(request=request, gist=gist, user=user)
        if is_mobile_device(request):
            return st('/m/gist/edit.html', **tdt)
        return st('/gist/edit.html', **tdt)

    def delete(self, request):
        gist = self.gist
        user = request.user
        if not user or user.username != gist.owner_id:
            raise AccessError()
        gist.delete()
        return request.redirect('/gist/%s' % user.username)

    def revisions(self, request):
        user = request.user
        gist = self.gist
        page = int(request.get_form_var('page', 1))
        skip = 3 * (page - 1)
        revlist = gist.get_revlist_with_renames(max_count=3, skip=skip)
        link_prev = _make_links(self.id, int(page) - 1, ext="revisions")
        if revlist:
            link_next = _make_links(self.id, int(page) + 1, ext="revisions")
        else:
            link_next = ''
        content = []
        for r in revlist:
            # FIXME: try-except ?
            content.append(gist.repo.get_diff(r.sha, rename_detection=True))
        tdt = {
            'request': request,
            'gist': gist,
            'content': content,
            'revlist': revlist,
            'link_prev': link_prev,
            'link_next': link_next,
            'user': user,
            'current_user': user,
        }
        return st('/gist/gist_revisions.html', **tdt)

    def forks(self, request):
        user = request.user
        gist = self.gist
        tdt = dict(request=request, gist=gist, user=user)
        return st('/gist/gist_forks.html', **tdt)

    def stars(self, request):
        user = request.user
        gist = self.gist
        tdt = dict(request=request, gist=gist, user=user)
        return st('/gist/gist_stars.html', **tdt)

    def fork(self, request):
        gist = self.gist
        new_gist = gist.fork(request.user.username)
        return request.redirect(new_gist.url)

    def star(self, request):
        GistStar.add(self.id, request.user.username)
        return request.redirect(self.gist.url)

    def unstar(self, request):
        star = GistStar.get_by_gist_and_user(self.id, request.user.username)
        if star:
            star.delete()
        return request.redirect(self.gist.url)

    def download(self, request):
        request.response.set_content_type("application/x-gzip")
        request.response.set_header("Content-Disposition",
                                    "filename=code_gist_%s.tar.gz" % self.id)
        return self.gist.repo.archive(name="code_gist_%s" % self.id)

    def re_index(self, request):
        index_a_gist(self.id)
        return request.redirect(self.gist.url)

    def _q_access(self, request):
        gist = self.gist
        user = request.user

        if not gist:
            raise TraversalError()

        if not gist.is_public:
            if not user or user.username != gist.owner_id:
                raise AccessError()


class RawGistUI(object):

    _q_exports = []

    def __init__(self, id):
        self.rev = ''
        self.gist = Gist.get(id)

    def _q_lookup(self, request, rev):
        self.rev = rev
        return RecursorGistUI(self.gist, self.rev)


class RecursorGistUI(object):

    _q_exports = []

    def __init__(self, gist, rev):
        self.gist = gist
        self.rev = rev
        self.path = ''

    def _q_lookup(self, request, path):
        self.path = path
        return self

    def __call__(self, request):
        try:
            # TODO: clean this
            text = self.gist.get_file(self.path, rev=self.rev)
        except IOError:
            raise TraversalError()
        if isinstance(text, bool) and text is False:
            raise TraversalError()
        resp = request.response
        resp.set_header("Content-Type", "text/plain; charset=utf-8")
        return text.encode('utf-8')


class UserGistUI:
    _q_exports = ['forked', 'starred', 'public', 'secret']

    def __init__(self, name):
        self.name = name
        self.user = User(name)

        current_user = request.user
        self.is_self = current_user and current_user.username == self.name
        ext = request.get_path().split('/')[-1]
        (self.page, self.start, self.link_prev, self.link_next, self.sort,
         self.direction) =\
            make_page_args(request, self.name, ext=ext)
        self.n_all = Gist.count_user_all(self.name, self.is_self)
        self.n_fork = Gist.count_user_fork(self.name)
        self.n_star = Gist.count_user_star(self.name)

        if self.sort not in ('created', 'updated') \
                or self.direction not in ('desc', 'asc'):
            raise TraversalError()

    def _render(self, request, gists):
        user = self.user
        tdt = {
            'request': request,
            'gists': gists,
            'user': user,
            'page': int(self.page),
            'link_prev': self.link_prev,
            'link_next': self.link_next,
            'n_all': self.n_all,
            'n_fork': self.n_fork,
            'n_star': self.n_star,
            'sort': self.sort,
            'direction': self.direction
        }
        if is_mobile_device(request):
            return st('/m/gist/user_gists.html', **tdt)
        return st('/gist/user_gists.html', **tdt)

    def _q_index(self, request):
        gists = Gist.gets_by_owner(
            self.name, is_self=self.is_self, start=self.start,
            limit=5, sort=self.sort, direction=self.direction)
        return self._render(request, gists)

    def forked(self, request):
        gists = Gist.forks_by_user(self.name, start=self.start,
                                   limit=5, sort=self.sort,
                                   direction=self.direction)
        return self._render(request, gists)

    def starred(self, request):
        gists = Gist.stars_by_user(self.name, start=self.start, limit=5)
        return self._render(request, gists)

    def public(self, request):
        gists = Gist.publics_by_user(self.name, start=self.start, limit=5,
                                     sort=self.sort, direction=self.direction)
        return self._render(request, gists)

    def secret(self, request):
        current_user = request.user
        if not current_user or current_user.username != self.name:
            return request.redirect('/gist/%s' % self.name)

        gists = Gist.secrets_by_user(self.name, start=self.start, limit=5,
                                     sort=self.sort, direction=self.direction)
        return self._render(request, gists)

    def _q_lookup(self, request, item):
        gid = item
        extend = None
        if item.count('.') == 1:
            gid, extend = item.split('.')

        if not gid.isdigit():
            raise TraversalError()

        gist = Gist.get(gid)

        if not gist or gist.owner_id != self.name:
            raise TraversalError()

        if extend == 'js':
            return GistEmbedUI(gid)

        return GistUI(gid)


EMBED_CSS = """
<link href=\"%s/static/css/highlight.css\" rel=\"stylesheet\">
<link href=\"%s/static/css/embed.css\" rel=\"stylesheet\">
""" % (DOMAIN, DOMAIN)

EMBED_HEAD = "<div id=\"gist%s\" class=\"gist\">"
EMBED_FOOTER = "</div>"

SRC_FORMAT = """
<div class=\"gist-data gist-syntax\">
  <div class=\"gist-file\">
    <div class=\"data\"> %s </div>
    <div class=\"gist-meta\">
      <a href=\"%s/gist/%s/raw/master/%s\" style=\"float:right\">view raw</a>
      <a href=\"%s/gist/%s#%s\" style=\"float:right; margin-right:10px; color:#666;\">%s</a>  # noqa
      <a href=\"%s\">This Gist</a> brought to you by <a href=\"%s\">Code</a>.
    </div>
  </div>
</div>
"""


class GistEmbedUI(object):
    _q_exports = []

    def __init__(self, gist_id):
        self.gist_id = gist_id

    def __call__(self, request):
        resp = request.response
        resp.set_header("Content-Type", "text/javascript")
        resp.set_header('Expires', 'Sun, 1 Jan 2006 01:00:00 GMT')
        resp.set_header('Pragma', 'no-cache')
        resp.set_header('Cache-Control', 'must-revalidate, no-cache, private')
        if not self.gist_id.isdigit() or not Gist.get(self.gist_id):
            return "document.write('<span style=\"color:red;\">NOT EXIST GIST</span>')"  # noqa
        gist = Gist.get(self.gist_id)
        html = EMBED_CSS + EMBED_HEAD % gist.id
        for path in gist.files:
            path = path.encode('utf8')
            # TODO: clean this
            src = gist.get_file(path, rev='HEAD')
            src = highlight_code(path, src)
            src = src.replace('"', '\"').replace("'", "\'")
            html += SRC_FORMAT % (src, DOMAIN, gist.id, path, DOMAIN,
                                  gist.id, path, path, gist.url, DOMAIN)

        html += EMBED_FOOTER
        html = html.replace('\n', '\\n')
        return "document.write('%s')" % html


class GistCommentUI(object):

    _q_exports = []

    def __init__(self, gist_id):
        self.gist = Gist.get(gist_id)

    def _q_index(self, request):
        if request.method == 'POST':
            content = request.get_form_var('content', '')
            if content:
                GistComment.add(self.gist.id, request.user.username, content)
        return request.redirect(self.gist.url)

    def _q_lookup(self, request, comment_id):
        if request.method == 'POST':
            act = request.get_form_var('act', None)
            if act and act in ('delete', 'update'):
                comment = GistComment.get(comment_id)
                if act == 'delete' and comment:
                    if comment.can_delete(request.user.username):
                        comment.delete()
                        return json.dumps({'r': 1})
                    raise TraversalError(
                        "Unable to delete comment %s" % comment_id)
        return request.redirect(self.gist.url)


def _get_req_gist_data(request):
    _form = request.form
    desc = _form.get('desc', '')
    is_public = _form.get('gist_public', '1')
    gist_names = _form.get('gist_name', '')
    gist_contents = _form.get('gist_content', '')
    gist_oids = _form.get('oid', '')
    return (desc, is_public, gist_names, gist_contents, gist_oids)


def _make_links(name, page, ext=''):
    if page < 1:
        return ''
    if page and page >= 1:
        if ext:
            return '/gist/%s/%s/?page=%s' % (name, ext, page)
        else:
            return '/gist/%s/?page=%s' % (name, page)


def make_page_args(request, name, ext=''):
    page = request.get_form_var('page', 1)
    start = 5 * (int(page) - 1)
    link_prev = _make_links(name, int(page) - 1, ext=ext)
    link_next = _make_links(name, int(page) + 1, ext=ext)
    sort = request.get_form_var('sort', 'created')
    direction = request.get_form_var('direction', 'desc')
    return (page, start, link_prev, link_next, sort, direction)
