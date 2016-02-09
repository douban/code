# -*- coding: utf-8 -*-

import re
import os
import json
import urllib
from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import HttpResponseBadRequest
from django.http import StreamingHttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from vilya.libs.template import st
from vilya.models.consts import TEMP_BRANCH_MARKER


def _latest_update_branch(project, ref, user):
    from vilya.models.pull import PullRequest
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


def watch_index(request):
    from vilya.models.project import CodeDoubanProject
    """get all watches"""
    user = request.user
    if user:
        return HttpResponse(json.dumps([
            {'pid': str(p.id)}
            for p in CodeDoubanProject.get_watched_projects_by_user(user.name)]))  # noqa
    return HttpResponse('')


@csrf_exempt
def watch(request, id):
    from vilya.models.project import CodeDoubanProject
    from vilya.views.util import error_message

    def new(request, proj_id):
        user = request.user
        CodeDoubanProject.add_watch(proj_id, user.name)
        return HttpResponse(json.dumps({"ok": 1}))


    def remove(request, proj_id):
        user = request.user
        CodeDoubanProject.del_watch(proj_id, user.name)
        return HttpResponse(json.dumps({"ok": 1}))


    # FIXME: ugly fix
    def has_watched(request, proj_id):
        user = request.user
        if CodeDoubanProject.has_watched(proj_id, user.name):
            return HttpResponse(json.dumps({"ok": 1}))
        return HttpResponse(json.dumps({"ok": 0}))

    proj_id = id
    if request.method == "POST":
        return new(request, proj_id)
    elif request.method == "DELETE":
        return remove(request, proj_id)
    elif request.method == "GET":
        return has_watched(request, proj_id)
    else:
        return HttpResponse(error_message("bad request"))


@csrf_exempt
def fetch(request, id):
    from vilya.views.util import error_message
    from tasks import fetch_mirror_project
    if request.method == "POST":
        fetch_mirror_project(id)
        return HttpResponse(json.dumps({"ok": 1}))
    return HttpResponse(error_message("bad request"))


def watchers(request, username, projectname):
    from vilya.models.project import CodeDoubanProject
    name = '/'.join([username, projectname])
    project = CodeDoubanProject.get_by_name(name)
    projects = []
    user = request.user
    users = project.get_watch_users()
    return HttpResponse(st('watchers.html', **locals()))


def forkers(request, username, projectname):
    from vilya.models.project import CodeDoubanProject
    name = '/'.join([username, projectname])
    project = CodeDoubanProject.get_by_name(name)
    projects = project.get_forked_projects()
    user = request.user
    users = project.get_forked_users()
    return HttpResponse(st('watchers.html', **locals()))


def archive(request, username, projectname, revision):
    from vilya.models.project import CodeDoubanProject
    name = '/'.join([username, projectname])
    part = revision
    project = CodeDoubanProject.get_by_name(name)
    repo = project.repo
    sha = repo.sha(revision)
    if not sha:
        return HttpResponseBadRequest()

    ext = request.GET.get('ext')
    if ext == 'tar':
        response = StreamingHttpResponse(content_type='application/x-tar')
        response['Content-Disposition'] = "filename=%s.tar" % part
        response.streaming_content = repo.archive(part, ref=sha, ext=ext)
    elif ext == 'tar.gz':
        response = StreamingHttpResponse(content_type='application/x-gzip')
        response['Content-Disposition'] = "filename=%s.tar.gz" % part
        response.streaming_content = repo.archive(part, ref=sha)
    else:
        response = StreamingHttpResponse(content_type='application/x-gzip')
        response['Content-Disposition'] = "filename=%s.tar.gz" % part
        response.streaming_content = repo.archive(part, ref=sha)
    return response


class ProjectView(View):

    template_name = ''

    def get(self, request, *args, **kwargs):
        tdt = self.get_data(request, *args, **kwargs)
        return HttpResponse(st(self.template_name, **tdt))

    def get_common_data(self, request, name, revision, path):
        from vilya.models.project import CodeDoubanProject
        user = request.user
        project = CodeDoubanProject.get_by_name(name)

        ref = revision
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
            'rev': revision,
            'tags': tags,
            'blob_path': blob_path,
            'file_name': blob_path.rpartition('/')[-1],
            'request': request,
            'project': project,
            'project_name': name,
            'path': path,
            'path_breadcrumb': path_breadcrumb,
            'ref_type': ref_type,
            'blob_ref': ref,
            'ref': ref,
            'user': user,
        }
        return tdt


class ProjectBlobView(ProjectView):
    template_name = 'blob.html'

    def get_data(self, request, username, projectname, revision, path=''):
        from vilya.models.project import CodeDoubanProject
        ''' get blob view '''
        name = '/'.join([username, projectname])
        project = CodeDoubanProject.get_by_name(name)
        path = path.encode('utf-8')
        tdt = self.get_common_data(request, name, revision, path)
        ref = revision
        if ref is None:
            ref = project.default_branch
        last_commit = project.repo.get_last_commit(
            ref, path=path, no_merges=True) if ref and path else ''
        tdt.update({
            'lastcommit': last_commit,
        })
        return tdt


@method_decorator(csrf_exempt, name="dispatch")
class ProjectEditView(ProjectView):
    template_name = 'edit.html'

    def post(self, request, username, projectname, revision, path=''):
        from vilya.models.project import CodeDoubanProject
        name = '/'.join([username, projectname])
        project = CodeDoubanProject.get_by_name(name)
        path = path.encode('utf-8')
        rgf = request.POST.get
        errors = ''
        success = ''
        ref = revision
        user = request.user
        direct_edit_allowed = True
        if not user:
            direct_edit_allowed = False
        elif not project.has_push_perm(user.name):
            direct_edit_allowed = False
        if ref is None:
            ref = project.default_branch
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
                except AssertionError as err:
                    errors = 'Error updating file %s: REPO COULD BE CORRUPTED, FETCH IT MANUALLY AND CHECK' % err  # noqa
                redir = str('/%s/blob/%s/%s' % (name, revision, commit_fn))
                return HttpResponseRedirect(redir)
            else:
                reflog = TEMP_BRANCH_MARKER
                tmp_branch = project.repo.get_temp_branch()
                project.repo.commit_file(
                    tmp_branch, ref, user.name, user.email, message,
                    reflog, data)
                redir = '/%s/newpull/new?base_repo=%s&head_ref=%s' % (
                    name, name, urllib.quote(tmp_branch))
                return HttpResponseRedirect(redir)

    def get_data(self, request, username, projectname, revision, path=''):
        from vilya.models.project import CodeDoubanProject
        name = '/'.join([username, projectname])
        project = CodeDoubanProject.get_by_name(name)
        path = path.encode('utf-8')
        rgf = request.POST.get
        tdt = self.get_common_data(request, name, revision, path)
        errors = ''
        success = ''
        ref = revision
        user = request.user
        direct_edit_allowed = True
        if not user:
            direct_edit_allowed = False
        elif not project.has_push_perm(user.name):
            direct_edit_allowed = False
        if ref is None:
            ref = project.default_branch
        # FIXME: 跟本文件中的其他 get_last_commit 调用参数不一致？
        last_commit = project.repo.get_last_commit(ref)

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

        def _get_help_link(path):
            ext = os.path.splitext(path)[1]
            return _help_links.get(ext, _help_links['default'])

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
                raise Http404()
            tdt.update({
                'text': text.decode('utf8'),
                'newfile': False,
                'template_text': rgf('template_code', '').replace(r'\n', '\n'),
                'orig_hash': hash(text),
            })
        return tdt


class ProjectBlameView(ProjectView):
    template_name = 'blame.html'

    def get_data(self, request, username, projectname, revision, path=''):
        from vilya.models.project import CodeDoubanProject
        name = '/'.join([username, projectname])
        project = CodeDoubanProject.get_by_name(name)
        tdt = self.get_common_data(request, name, revision, path)
        ref = revision
        if ref is None:
            ref = project.default_branch
        blob_path = path.decode('utf-8')
        try:
            blame = project.repo.blame_file(ref, blob_path)
            commit = project.repo.get_commit(ref)
        except IOError:
            raise Http404()
        tdt.update({
            'blame': blame,
            'commit': commit,
        })
        return tdt


class ProjectRawView(ProjectView):
    template_name = 'patch.html'

    def get(self, request, username, projectname, revision, path=''):
        from vilya.libs.text import is_image, is_binary
        from vilya.models.project import CodeDoubanProject
        name = '/'.join([username, projectname])
        project = CodeDoubanProject.get_by_name(name)
        rev = revision
        if rev is None:
            rev = project.default_branch
        try:
            blob = project.repo.get_file(rev, path.decode('utf-8'))
        except IOError:
            raise Http404()
        if not blob:
            raise Http404("No content found")

        response = StreamingHttpResponse()
        if is_image(path):
            if path.endswith('svg'):
                response['Content-Type'] = "image/svg+xml"
            else:
                response['Content-Type'] = "image/jpeg"
            response['Expires'] = "Sun, 1 Jan 2006 01:00:00 GMT"
            response['Pragma'] = "no-cache"
            response['Cache-Control'] = "must-revalidate, no-cache, private"
            response.streaming_content = blob.data
            return response
        if path.endswith('.pdf'):
            response['Content-Type'] = "application/pdf"
            response.streaming_content = blob.data
            return response
        if is_binary(path):
            response['Content-Type'] = "application/octet-stream"
            response['Content-Disposition'] = "attachment;filename=%s" % path.split('/')[-1]
            response['Content-Transfer-Encoding'] = "binary"
            response.streaming_content = blob.data
            return response

        response['Content-Type'] = "text/plain;charset=utf-8"
        response.streaming_content = blob.data.encode('utf8')
        return response


class ProjectTreeView(ProjectView):
    template_name = 'tree.html'

    def get_data(self, request, username, projectname, revision, path=''):
        from vilya.libs.text import format_md_or_rst
        from vilya.models.mirror import CodeDoubanMirror
        from vilya.models.project import CodeDoubanProject
        name = '/'.join([username, projectname])
        project = CodeDoubanProject.get_by_name(name)
        if not project:
            raise Http404("Wrong path for tree %s" % path)
        if project.is_mirror_project:
            mirror = CodeDoubanMirror.get_by_project_id(project.id)
            if not mirror.is_clone_completed:
                return st('/projects/mirror_cloning.html', **locals())
        if not project.repo:
            raise Http404("Wrong path for tree %s" % path)
        ref = revision
        if not ref:
            ref = project.default_branch

        tree_path = path.decode('utf-8')
        last_commit = project.repo.get_last_commit(ref, path=path) if ref else ''
        tdt = self.get_common_data(request, name, ref, path)
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
            raise Http404("Wrong path for tree %s" % path)

        if isinstance(tree, basestring):
            raise Http404("Got a blob instead of a tree")

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
            'is_go_get': request.GET.get('go-get', 0)
        })
        return tdt


class ProjectCommitsView(ProjectView):
    template_name = 'commits.html'

    def get_data(self, request, username, projectname, revision, path=''):
        from vilya.models.release import get_release
        from vilya.models.ngit.commits_graph import generate_graph_data
        from vilya.models.comment import Comment
        from vilya.models.project import CodeDoubanProject
        NB_COMMITS_PER_PAGE = 20
        name = '/'.join([username, projectname])
        project = CodeDoubanProject.get_by_name(name)
        path = path.encode('utf-8')
        show_merges = request.GET.get('show_merges', None)
        if show_merges and show_merges.isdigit():
            show_merges = int(show_merges)
        else:
            show_merges = 0 if path else 1

        # Keep start_rev for older links
        start_rev = request.GET.get('start_rev', None)
        if start_rev and not revision:
            revision = start_rev
        if not revision:
            revision = project.default_branch
        page = int(request.GET.get('page', 1))
        author = request.GET.get('author', None)
        query = request.GET.get('query', None)
        skip = NB_COMMITS_PER_PAGE * (page - 1)
        tdt = self.get_common_data(request, name, revision, path)
        revlist = project.repo.get_commits(revision, max_count=NB_COMMITS_PER_PAGE,
                                        skip=skip, path=path, author=author,
                                        query=query,
                                        no_merges=(not show_merges))

        def _get_comment_counts(revlist, proj_id):
            def _pack(sha):
                return [(c.author, c.short_content)
                        for c in Comment.gets_by_proj_and_ref(proj_id, sha)]
            return dict((rev.sha, _pack(rev.sha)) for rev in revlist)

        comment_counts = _get_comment_counts(revlist, project.id)

        # handle renamed file
        renames = dict()
        if revlist:  # and not next:
            oldcommit = revlist[-1]
            renames = project.repo.get_renamed_files(oldcommit.sha)
        rename_from = renames.get(path, '')

        graph_data = generate_graph_data(revlist)
        older_revlist = project.repo.get_commits(revision,
                                                max_count=NB_COMMITS_PER_PAGE,
                                                skip=(NB_COMMITS_PER_PAGE * page),
                                                path=path, author=author,
                                                query=query)

        release = get_release(project.repository)

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

        tdt.update({
            'comment_counts': comment_counts,
            'rename_from': rename_from,
            'author': author,
            'query': query,
            'revlist': revlist,
            'renames': renames,
            'page': page,
            'link_prev': _make_links(project, revision, author, path, page - 1, query),
            'link_next': _make_links(project, revision, author, path, page + 1, query)
            if older_revlist else False,
            'release': release,
            'graph_data': graph_data,
        })
        return tdt


def browsefiles(request, username, projectname):
    from vilya.models.project import CodeDoubanProject

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

    name = '/'.join([username, projectname])

    if 'json' in request.environ['HTTP_ACCEPT']:
        output = 'json'
    else:
        output = 'html'
    project = CodeDoubanProject.get_by_name(name)
    user = request.user
    path = request.GET.get('path', '')
    rev = request.GET.get('rev', project.default_branch)
    allfiles = project.repo.get_tree(rev, path=path)
    allfiles = [_add_file_type_and_warns(f) for f in allfiles]
    errors = ''
    ref = rev
    if ref is None:
        ref = project.default_branch
    branches = project.repo.branches
    tags = project.repo.tags
    ref_type = 'branch' if ref in branches else 'tag' \
                if ref in tags else 'tree'
    if output == 'json':
        return HttpResponse(json.dumps(allfiles))
    else:
        return HttpResponse(st('browsefiles.html', **locals()))


@csrf_exempt
def codereview_delete(request, username, projectname, id):
    from vilya.models.linecomment import PullLineComment
    comment = PullLineComment.get(id)
    if not comment:
        raise Http404("Unable to find comment %s" % id)

    user = request.user
    if comment.author == user.name:
        ok = comment.delete()
        if ok:
            return HttpResponse(json.dumps({'r': 1}))  # FIXME: 这里 r=1 表示成功，跟其他地方不统一
    return HttpResponse(json.dumps({'r': 0}))


@csrf_exempt
def codereview_edit(request, username, projectname, id):
    from vilya.models.linecomment import PullLineComment
    from vilya.models.project import CodeDoubanProject
    name = '/'.join([username, projectname])
    comment = PullLineComment.get(id)
    if not comment:
        raise Http404("Unable to find comment %s" % id)

    user = request.user
    project = CodeDoubanProject.get_by_name(name)
    content = request.POST.get(
        'pull_request_review_comment', '').decode('utf-8')
    if comment.author == user.name:
        comment.update(content)
        linecomment = PullLineComment.get(comment.id)
        pullreq = True
        return HttpResponse(json.dumps(dict(
            r=0, html=st('/pull/ticket_linecomment.html', **locals()))))
    return HttpResponse(json.dumps(dict(r=1)))


def comment(request, username, projectname):
    from vilya.models.comment import latest
    return HttpResponse("Last comments list TODO" + str(latest()))


@csrf_exempt
def comment_new(request, username, projectname):
    from vilya.models.project import CodeDoubanProject
    from vilya.models.comment import Comment
    name = '/'.join([username, projectname])
    project = CodeDoubanProject.get_by_name(name)
    user = request.user
    ref = request.POST.get('ref')
    assert ref, "comment ref cannot be empty"
    content = request.POST.get('content', '')
    new_comment = Comment.add(project, ref, user.name, content)

    return HttpResponseRedirect("/%s/commit/%s#%s" %
                            (name, ref, new_comment.uid))


@csrf_exempt
def comment_delete(request, username, projectname, id):
    from vilya.models.comment import Comment
    if request.method == 'DELETE':
        # FIXME: 不用验证user？
        ok = Comment.delete(id)
        if not ok:
            raise Http404("Unable to delete comment %s" % id)
        return HttpResponse('')
    return HttpResponse("Display comment %s TODO" % id)


def compare_index(request, username, projectname):
    return HttpResponseBadRequest('please provide valid start & end revisions: /compare/start...end')


def compare_range(request, username, projectname, range):
    from itertools import groupby
    from vilya.models.project import CodeDoubanProject
    from vilya.models.comment import Comment
    name = '/'.join([username, projectname])
    revrange = range
    project = CodeDoubanProject.get_by_name(name)
    current_user = request.user
    try:
        sha1, sha2 = revrange.split('...')
    except ValueError:
        raise Http404(
            'please provide valid start & end revisions: /compare/sha1...sha2')  # noqa
    commits = project.repo.get_commits(sha2, sha1)
    if commits is False:
        raise Http404()
    lasttime = commits and commits[0].author_time.strftime(
        "%Y-%m-%d %H:%M:%S") or 'UNKNOWN'
    grouped_commits = groupby(commits, lambda c: c.author_time.date())
    n_commits = len(commits)
    n_authors = len(set(c.author.username for c in commits))
    diff = project.repo.get_diff(sha2,
                                 from_ref=sha1,
                                 rename_detection=True)
    #diffs = project.git.get_3dot_diff(sha1, sha2)
    n_files = diff.length if diff else 0
    comments = []
    for ci in commits:
        comments.extend(Comment.gets_by_proj_and_ref(project.id, ci.sha))
    branches = project.repo.branches
    tags = project.repo.tags
    ref = project.default_branch
    n_comments = len(comments)
    ref_type = 'branch' if ref in branches else 'tag' \
                if ref in tags else 'tree'
    return HttpResponse(st('compare.html', **locals()))
