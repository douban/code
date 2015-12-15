# -*- coding: utf-8 -*-

from __future__ import absolute_import

import re
import os
import urllib

from quixote.errors import TraversalError

from vilya.libs.template import st
from vilya.libs.text import format_md_or_rst
from vilya.libs.text import is_image, is_binary
from vilya.models.pull import PullRequest
from vilya.models.project import CodeDoubanProject
from vilya.models.comment import Comment
from vilya.models.mirror import CodeDoubanMirror
from vilya.models.release import get_release
from vilya.models.consts import TEMP_BRANCH_MARKER
from vilya.models.ngit.commits_graph import generate_graph_data

NB_COMMITS_PER_PAGE = 20

_q_exports = []

# Please change help links to better ones. I think best would be
# some code projects with cheatsheets and links to official ressources
# -- guibog
_help_links = {
    '.rst': 'http://code.dapps.douban.com/metadoc/docs/',
    '.md': 'http://daringfireball.net/projects/markdown/',
    '.py': 'http://docs.python.org/2.7/',
    '.html': 'http://docs.makotemplates.org/en/latest/',
    '.css': 'http://www.w3.org/Style/CSS/Overview.en.html',
    '.js': 'https://developer.mozilla.org/en/docs/JavaScript',
    '.yaml': 'http://www.yaml.org/refcard.html',
    'default': 'http://www.wikipedia.org/'
}


def _get_breadcrumb(path):
    subpath = []

    def get_subpath(prev_path, path):
        if path:
            path = path.strip('/')
            prev_path = prev_path.strip('/')
            cur, sep, next = path.partition('/')
            if prev_path:
                cur_path = '%s/%s' % (prev_path, cur)
            else:
                cur_path = cur
            subpath.append({'title': cur.decode(
                'utf-8'), 'path': cur_path.decode('utf-8')})
            get_subpath(cur_path, next)

    get_subpath('', path)
    return subpath


def _get_tmpl_tree(tmpl_target, ref, path, project_name, request):
    project = CodeDoubanProject.get_by_name(project_name)
    if not project:
        raise TraversalError("Wrong path for tree %s" % path)
    if project.is_mirror_project:
        mirror = CodeDoubanMirror.get_by_project_id(project.id)
        if not mirror.is_clone_completed:
            return st('/projects/mirror_cloning.html', **locals())
    if not project.repo:
        raise TraversalError("Wrong path for tree %s" % path)
    if not ref:
        ref = project.default_branch

    tree_path = path.decode('utf-8')
    last_commit = project.repo.get_last_commit(ref, path=path) if ref else ''
    tdt = _tmpl_common_data(ref, path, project_name, request)
    user = tdt['user']
    if user is not None:
        username = user.username
        cur_user_project = project.get_forked_project(username)
        if cur_user_project is not None:
            latest_branch = _latest_update_branch(
                cur_user_project, ref, user)
            if latest_branch:
                cur_user_latest_branch_name = '{0}:{1}'.format(
                    username, latest_branch)
                tdt['latest_update_branch'].append(
                    (cur_user_project, cur_user_latest_branch_name,
                     latest_branch))
    tdt.update({
        'lastcommit': last_commit,
    })

    tree = []
    is_empty = True
    if last_commit:
        tree = project.repo.get_tree(ref, path)
        is_empty = False if tree else True

    if is_empty and not project.repo.is_empty:
        raise TraversalError("Wrong path for tree %s" % path)

    if isinstance(tree, basestring):
        raise TraversalError("Got a blob instead of a tree")

    # Add README code to tree if any
    for item in tree:
        if (item['type'] == 'blob'
            and (item['name'] == 'README'
                 or item['name'].startswith('README.'))):
            readme_content = project.repo.get_file_by_ref(
                "%s:%s" % (ref, item['path'])
            )
            tdt.update({
                'readme_content': format_md_or_rst(item['path'],
                                                   readme_content,
                                                   project.name),
            })
            break

    tdt.update({
        'tree': tree,
        'tree_path': tree_path,
        'is_empty': is_empty,
    })
    return st(tmpl_target, **tdt)


def _latest_update_branch(project, ref, user):
    if user:
        get_pr = user.get_user_submit_pull_requests
        latest_tickets = get_pr(limit=5, is_closed=False) + get_pr(
            limit=5, is_closed=True)
        latest_tickets = filter(None, [PullRequest.get_by_ticket(t)
                                       for t in latest_tickets if t.project])
        has_pr_branches = [t.from_ref for t in latest_tickets]
    else:
        has_pr_branches = []
    latest_update_branches = filter(lambda b: b[1] != ref
                                    and b[1] not in has_pr_branches,
                                    project.repo.get_latest_update_branches())
    latest_update_branch = (latest_update_branches[0][1]
                            if latest_update_branches else '')
    return latest_update_branch


def _tmpl_common_data(rev, path, project_name, request):
    user = request.user
    project = CodeDoubanProject.get_by_name(project_name)

    ref = rev
    if ref is None:
        ref = project.default_branch

    branches = project.repo.branches
    tags = project.repo.tags
    ref_type = 'tree'
    if ref in branches:
        ref_type = 'branch'
    elif ref in tags:
        ref_type = 'tag'

    blob_path = path.decode('utf-8')
    path_breadcrumb = _get_breadcrumb(path)

    latest_branch = _latest_update_branch(project, ref, user)
    if latest_branch:
        latest_update_branch = [(project, latest_branch, latest_branch)]
    else:
        latest_update_branch = []

    tdt = {
        'errors': '',
        'branches': branches,
        'latest_update_branch': latest_update_branch,
        'rev': rev,
        'tags': tags,
        'blob_path': blob_path,
        'file_name': blob_path.rpartition('/')[-1],
        'request': request,
        'project': project,
        'project_name': project_name,
        'path': path,
        'path_breadcrumb': path_breadcrumb,
        'ref_type': ref_type,
        'blob_ref': ref,
        'ref': ref,
        'user': user,
    }
    return tdt


def _get_tmpl_blob(tmpl_target, rev, path, project_name, request):
    ''' get blob view '''
    tdt = _tmpl_common_data(rev, path, project_name, request)
    project = CodeDoubanProject.get_by_name(project_name)
    ref = rev
    if ref is None:
        ref = project.default_branch
    last_commit = project.repo.get_last_commit(
        ref, path=path, no_merges=True) if ref and path else ''
    tdt.update({
        'lastcommit': last_commit,
    })
    return st(tmpl_target, **tdt)


def _get_tmpl_blame(tmpl_target, rev, path, project_name, request):
    tdt = _tmpl_common_data(rev, path, project_name, request)
    project = CodeDoubanProject.get_by_name(project_name)
    ref = rev
    if ref is None:
        ref = project.default_branch
    blob_path = path.decode('utf-8')
    try:
        blame = project.repo.blame_file(ref, blob_path)
        commit = project.repo.get_commit(ref)
    except IOError:
        raise TraversalError()
    tdt.update({
        'blame': blame,
        'commit': commit,
    })
    return st(tmpl_target, **tdt)


def _get_tmpl_raw(tmpl_target, rev, path, project_name, request):
    project = CodeDoubanProject.get_by_name(project_name)
    if rev is None:
        rev = project.default_branch
    try:
        blob = project.repo.get_file(rev, path.decode('utf-8'))
    except IOError:
        raise TraversalError()
    if not blob:
        raise TraversalError("No content found")
    resp = request.response
    if is_image(path):
        if path.endswith('svg'):
            resp.set_header("Content-Type", "image/svg+xml")
        else:
            resp.set_header("Content-Type", "image/jpeg")
        resp.set_header('Expires', 'Sun, 1 Jan 2006 01:00:00 GMT')
        resp.set_header('Pragma', 'no-cache')
        resp.set_header('Cache-Control', 'must-revalidate, no-cache, private')
        return blob.data
    if path.endswith('.pdf'):
        resp.set_header("Content-Type", "application/pdf")
        return blob.data
    if is_binary(path):
        resp.set_header("Content-Type", "application/octet-stream")
        resp.set_header("Content-Disposition",
                        "attachment;filename=%s" % path.split('/')[-1])
        resp.set_header("Content-Transfer-Encoding", "binary")
        return blob.data
    resp.set_header("Content-Type", "text/plain;charset=utf-8")
    return blob.data.encode('utf8')


def _get_tmpl_edit(tmpl_target, rev, path, project_name, request):
    rgf = request.get_form_var
    tdt = _tmpl_common_data(rev, path, project_name, request)
    project = CodeDoubanProject.get_by_name(project_name)
    errors = ''
    success = ''
    ref = rev
    user = request.user
    direct_edit_allowed = True
    if not user:
        direct_edit_allowed = False
    elif not project.has_push_perm(user.name):
        direct_edit_allowed = False
    if ref is None:
        ref = project.default_branch
    if request.method == 'POST':
        source = rgf('code')
        message = rgf('message')
        desc = rgf('desc')
        if message == '':
            errors = u'commit summary不能为空'
        if rgf('newfile') and not re.match('^[a-zA-Z_\-0-9.]+$', rgf('newfilename', '')):
            errors = 'new filename incorrect: (%s)' % rgf('newfilename')
        if not errors:
            if rgf('newfile'):
                commit_fn = os.path.join(path, rgf('newfilename'))
                assert not project.repo.get_commit(
                    "%s:%s" % (ref, commit_fn)), "file_already_exist"
            else:
                commit_fn = rgf('filename')
            message = "%s\n\n%s" % (message, desc)
            message = message.decode("utf8")
            data = []
            data.append([commit_fn, source, 'insert'])
            if direct_edit_allowed:
                reflog = 'commit_one_file on %s' % ref
                assert ref == 'master' or ref in project.repo.branches, \
                    "commit online allowed on existing branches only"
                try:
                    project.repo.commit_file(
                        ref, ref, user.name, user.email, message, reflog, data)
                    success = u'提交成功'
                except AssertionError, err:
                    errors = 'Error updating file %s: REPO COULD BE CORRUPTED, FETCH IT MANUALLY AND CHECK' % err  # noqa
                redir = str('/%s/blob/%s/%s' % (project_name, rev, commit_fn))
                return request.redirect(redir)
            else:
                reflog = TEMP_BRANCH_MARKER
                tmp_branch = project.repo.get_temp_branch()
                project.repo.commit_file(
                    tmp_branch, ref, user.name, user.email, message,
                    reflog, data)
                redir = '/%s/newpull/new?base_repo=%s&head_ref=%s' % (
                    project_name, project_name, urllib.quote(tmp_branch))
                return request.redirect(redir)
    # FIXME: 跟本文件中的其他 get_last_commit 调用参数不一致？
    last_commit = project.repo.get_last_commit(ref)
    tdt.update({
        'success': success,
        'errors': errors,
        'direct_edit_allowed': direct_edit_allowed,
        'help_link': _get_help_link(path),
        'lastcommit': last_commit,
    })
    if rgf('newfile'):
        tdt.update({
            'newfile': True,
            'newfilename': rgf('newfilename', ''),
            'text': rgf('code', ''),
            'template_text': rgf('template_code', '').replace(r'\n', '\n'),
            'orig_hash': False,
        })
    else:
        try:
            text = project.repo.get_file_by_ref(
                "%s:%s" % (ref, path.decode('utf-8')))
        except IOError:
            raise TraversalError()
        tdt.update({
            'text': text.decode('utf8'),
            'newfile': False,
            'template_text': rgf('template_code', '').replace(r'\n', '\n'),
            'orig_hash': hash(text),
        })
    return st(tmpl_target, **tdt)


def _get_help_link(path):
    ext = os.path.splitext(path)[1]
    return _help_links.get(ext, _help_links['default'])


def _get_tmpl_commits(tmpl_target, rev, path, project_name, request):
    project = CodeDoubanProject.get_by_name(project_name)
    show_merges = request.get_form_var('show_merges', None)
    if show_merges and show_merges.isdigit():
        show_merges = int(show_merges)
    else:
        show_merges = 0 if path else 1

    # Keep start_rev for older links
    start_rev = request.get_form_var('start_rev', None)
    if start_rev and not rev:
        rev = start_rev
    if not rev:
        rev = project.default_branch
    page = int(request.get_form_var('page', 1))
    author = request.get_form_var('author', None)
    query = request.get_form_var('query', None)
    skip = NB_COMMITS_PER_PAGE * (page - 1)
    tdt = _tmpl_common_data(rev, path, project_name, request)
    revlist = project.repo.get_commits(rev, max_count=NB_COMMITS_PER_PAGE,
                                       skip=skip, path=path, author=author,
                                       query=query,
                                       no_merges=(not show_merges))
    comment_counts = _get_comment_counts(revlist, project.id)

    # handle renamed file
    renames = dict()
    if revlist:  # and not next:
        oldcommit = revlist[-1]
        renames = project.repo.get_renamed_files(oldcommit.sha)
    rename_from = renames.get(path, '')

    graph_data = generate_graph_data(revlist)

    older_revlist = project.repo.get_commits(rev,
                                             max_count=NB_COMMITS_PER_PAGE,
                                             skip=(NB_COMMITS_PER_PAGE * page),
                                             path=path, author=author,
                                             query=query)

    release = get_release(project.repository)

    tdt.update({
        'comment_counts': comment_counts,
        'rename_from': rename_from,
        'author': author,
        'query': query,
        'revlist': revlist,
        'renames': renames,
        'page': page,
        'link_prev': _make_links(project, rev, author, path, page - 1, query),
        'link_next': _make_links(project, rev, author, path, page + 1, query)
        if older_revlist else False,
        'release': release,
        'graph_data': graph_data,
    })
    return st(tmpl_target, **tdt)


def _make_links(project, rev, author, path, page, query):
    if page < 1:
        return False
    params = []
    if author:
        params.append(('author', author))
    if page and page != 1:
        params.append(('page', page))
    if query:
        params.append(('query', query))
    querystring = urllib.urlencode(params)
    querystring = '?' + querystring if querystring else ''
    return "/{project.name}/commits/{rev}/{path}{querystring}".format(
        project=project, rev=rev, path=path, querystring=querystring
    )


def _get_comment_counts(revlist, proj_id):
    def _pack(sha):
        return [(c.author, c.short_content)
                for c in Comment.gets_by_proj_and_ref(proj_id, sha)]
    return dict((rev.sha, _pack(rev.sha)) for rev in revlist)

# target, getter
_all_views = {
    'blob': ('blob.html', _get_tmpl_blob),
    'blame': ('blame.html', _get_tmpl_blame),
    'raw': ('patch.html', _get_tmpl_raw),
    'edit': ('edit.html', _get_tmpl_edit),
    'tree': ('tree.html', _get_tmpl_tree),
    'commits': ('commits.html', _get_tmpl_commits),
}


class SourceUI(object):

    _q_exports = []

    def __init__(self, proj, view):
        self.proj = proj
        self.view = view

    def _q_lookup(self, request, rev):
        return RecursorUI(self.proj, rev, self.get_content)

    def direct_index(self, request):
        project = CodeDoubanProject.get_by_name(self.proj)
        if not project:
            raise TraversalError()
        return self.get_content(None, '', request)

    def get_content(self, rev, path, request):
        # TODO use a wrapper instead:
        # get common vars
        # merge specials
        if self.view not in _all_views:
            raise TraversalError()

        tmpl_target = _all_views[self.view][0]
        tmpl_getter = _all_views[self.view][1]

        # PJAX
        if request.environ.get('HTTP_X_PJAX', False):
            request.response.set_header('X-PJAX-VERSION', "v1")
            tmpl_target = 'pjax_' + tmpl_target

        return tmpl_getter(tmpl_target, rev, path, self.proj, request)


class RecursorUI(object):

    _q_exports = []

    def __init__(self, proj, rev, get_content):
        self.parts = [rev]
        self.proj = proj
        self.get_content = get_content
        self.project = CodeDoubanProject.get_by_name(self.proj)

    def _q_lookup(self, request, part):
        self.parts.append(part)
        return self

    def _q_index(self, request):
        if not self.project:
            raise TraversalError()
        rev, path = self.split_rev_from_path()
        return self.get_content(rev, path, request)

    def split_rev_from_path(self):
        for branch in self.project.repo.branches:
            bsp = branch.split('/')
            if self.parts[0:len(bsp)] == bsp:
                rev = branch
                path_part = self.parts[len(bsp):]
                break
        else:
            rev = self.parts[0]
            path_part = self.parts[1:]
        return rev, '/'.join(path_part)

    def __call__(self, request):
        if not self.project:
            raise TraversalError()
        rev, path = self.split_rev_from_path()
        return self.get_content(rev, path, request)


def report_deprecation(request, view):
    referer = request.environ.get('HTTP_REFERER', '')
    if 'brook' in referer:
        from_ = 'from brook'
    else:
        from_ = request.environ.get(
            'RAW_URI', '???').strip('/').partition('/')[0]
    try:
        raise DeprecationWarning("Old url for source code %s" % view)
    except DeprecationWarning, err:
        from vilya.libs.store import report_error_to_sentry
        report_error_to_sentry(
            err, "@guibog: Old url for source code %s from %s - v07" % (
                view, from_))
