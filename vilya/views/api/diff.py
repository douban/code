# -*- coding: utf-8 -*-

from quixote.errors import TraversalError
from vilya.libs.template import st
from vilya.views.util import jsonize

from vilya.models.pull import PullRequest
from vilya.models.project import CodeDoubanProject
from vilya.models.linecomment import CommitLineComment, PullLineComment


class DiffMixin(object):

    def _toggle_whitespace(self, request):
        raise NotImplementedError('Subclasses should implement this!')

    @jsonize
    def moreline(self, request):
        resp = request.response
        resp.set_header("Content-Type", "application/json")

        MAX_CONTEXT_LINES = 10
        current_user = request.user
        project = self.project
        old_sha = request.get_form_var('old_sha')
        old_path = request.get_form_var('old_path')
        _type = request.get_form_var('type')
        old_start = request.get_form_var('old_start')
        new_start = request.get_form_var('new_start')
        old_end = request.get_form_var('old_end')
        new_end = request.get_form_var('new_end')

        old_start = old_start and old_start.isdigit() and int(old_start)
        new_start = new_start and new_start.isdigit() and int(new_start)
        old_end = old_end and old_end.isdigit() and int(old_end)
        new_end = new_end and new_end.isdigit() and int(new_end)

        if _type == 'after':
            context_old_start = old_end - MAX_CONTEXT_LINES + 1
            context_new_start = new_end - MAX_CONTEXT_LINES + 1
            context_old_end = old_end
            context_new_end = new_end
            if context_old_start <= old_start:
                _type = 'all'
        elif _type == 'before':
            context_old_start = old_start
            context_new_start = new_start
            context_old_end = old_start + MAX_CONTEXT_LINES - 1
            context_new_end = new_start + MAX_CONTEXT_LINES - 1
            if context_old_end >= old_end:
                _type = 'all'
        if _type == 'all':
            context_old_start = old_start
            context_new_start = new_start
            context_old_end = old_end
            context_new_end = new_end

        context_lines = project.repo.get_contexts(old_sha, old_path,
                                                  context_old_start,
                                                  context_old_end + 1)
        html = st('/widgets/diff/diff_lines.html', **locals())
        return dict(r=0, html=html)

    def prepare(self, request):
        project = self.project
        filepath = request.get_form_var('filepath')
        new_filepath = request.get_form_var('new_filepath')

        if new_filepath:
            paths = [filepath, new_filepath]
        else:
            paths = [filepath]

        whitespace = request.get_form_var('w', '0')
        if whitespace.isdigit() and int(whitespace) == 1:
            ignore_space = True
        else:
            ignore_space = False

        return project, paths, ignore_space

    @jsonize
    def toggle_whitespace(self, request, sha1=None, context_lines=None,
                          **kwargs):
        project, paths, ignore_space = self.prepare(request)
        diff = self._toggle_whitespace(
            request, project, paths, ignore_space, sha1=sha1,
            context_lines=context_lines, **kwargs)
        return self.send_response(request, diff)

    def send_response(self, request, diff):
        resp = request.response
        resp.set_header("Content-Type", "application/json")
        current_user = request.user
        kwargs = {
            'diff': diff,
            'current_user': current_user,
        }
        html = st('/widgets/diff/diff_full.html', **kwargs)

        return dict(r=0, html=html)

    def fulltext(self, request, sha1=None, **kwargs):
        return self.toggle_whitespace(request, sha1=sha1, context_lines=9999,
                                      **kwargs)


class CommitDiffMixin(DiffMixin):

    def _toggle_whitespace(self, request, project, paths, ignore_space,
                           **kwargs):
        sha1 = kwargs.get('sha1')
        context_lines = kwargs.get('context_lines')
        ref = sha1
        if ref is None:
            ref = project.default_branch
        linecomments = CommitLineComment.gets_by_target_and_ref(project.id,
                                                                ref)
        kw = {
            'ref': sha1,
            'paths': paths,
            'ignore_space': ignore_space,
            'rename_detection': True,
            'linecomments': linecomments
        }
        if context_lines is not None:
            kw.update({'context_lines': context_lines})
        try:
            commit = project.repo.get_commit(sha1)
            # get_diff 默认与 parent diff
            diff = project.repo.get_diff(**kw)
            if not commit:
                raise TraversalError("not a valid commit ref")
        except IOError:
            raise TraversalError()
        return diff


class PullDiffMixin(DiffMixin):

    def _toggle_whitespace(self, request, project, paths, ignore_space,
                           **kwargs):
        # For pull/new
        from_proj = request.get_form_var('from_proj')
        from_ref = request.get_form_var('from_ref')
        to_ref = request.get_form_var('to_ref')
        to_proj = request.get_form_var('to_proj')

        sha1 = kwargs.get('sha1')
        context_lines = kwargs.get('context_lines')
        ref = sha1
        if ref is None:
            ref = project.default_branch
        if hasattr(self, 'ticket'):
            pullreq = PullRequest.get_by_proj_and_ticket(
                project.id, self.ticket.ticket_number)
            linecomments = PullLineComment.gets_by_target(self.ticket.id)
        else:
            from_proj = CodeDoubanProject.get_by_name(from_proj)
            parent_proj = from_proj.get_forked_from()
            if to_proj:
                to_proj = CodeDoubanProject.get_by_name(to_proj)
            elif parent_proj:
                to_proj = parent_proj
            else:
                to_proj = from_proj
            pullreq = PullRequest.open(from_proj, from_ref, to_proj, to_ref)
            linecomments = []

        kw = {
            'paths': paths,
            'rename_detection': True,
            'linecomments': linecomments
        }
        if context_lines is not None:
            kw.update({'context_lines': context_lines})
        diff = pullreq.get_diff(**kw)
        return diff


class PullDiffUI(PullDiffMixin):
    _q_exports = ['fulltext', 'moreline', 'toggle_whitespace']

    def __init__(self, request, proj_name):
        self.project = CodeDoubanProject.get_by_name(proj_name)
