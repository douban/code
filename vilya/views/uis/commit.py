# -*- coding: utf-8 -*-

from quixote.errors import TraversalError

from vilya.libs.template import st
from vilya.models.project import CodeDoubanProject
from vilya.models.comment import Comment
from vilya.models.linecomment import CommitLineComment
from vilya.views.api.diff import CommitDiffMixin


class CommitUI(CommitDiffMixin):

    _q_exports = []

    def __init__(self, proj_name):
        self.proj_name = proj_name
        self.project = CodeDoubanProject.get_by_name(self.proj_name)
        if not self.project:
            raise TraversalError()
        self.parts = []

    def _q_lookup(self, request, part):
        self.parts.append(part)
        return self

    def _q_index(self, request):
        if len(self.parts) == 1:
            return self.source(request, self.parts[0])
        elif len(self.parts) == 2:
            sha1 = self.parts[0]
            _type = self.parts[1]
            if _type == 'fulltext':
                return self.fulltext(request, sha1)
            elif _type == 'moreline':
                return self.moreline(request)
            elif _type == 'toggle_whitespace':
                return self.toggle_whitespace(request, sha1)
            raise TraversalError()
        elif len(self.parts) > 2 and self.parts[1] == 'src':
            sha1 = self.parts[0]
            path = '/'.join(self.parts[2:])
            return self.source(request, sha1, path=path)
        return request.redirect('/%s/commit/%s'
                                % (self.proj_name,
                                   self.project.default_branch))

    def source(self, request, sha1, path=None):
        current_user = request.user
        # guibog 20120815 some inherited templates need current user as user
        user = request.user
        project = self.project
        if sha1.count('.') == 1:
            sha, diff_type = sha1.split('.')
            resp = request.response
            resp.set_header("Content-Type", "text/plain")
            if diff_type == 'patch':
                text = project.repo.get_patch_file(sha)
                return text.encode('utf-8')
            elif diff_type == 'diff':
                text = project.repo.get_diff_file(sha)
                return text.encode('utf-8')

        ref = sha1
        if ref is None:
            ref = project.default_branch
        branches = project.repo.branches
        tags = project.repo.tags
        ref_type = ('branch' if ref in branches else 'tag'
                    if ref in tags else 'tree')

        comments = Comment.gets_by_proj_and_ref(project.id, ref)
        linecomments = CommitLineComment.gets_by_target_and_ref(project.id,
                                                                ref)

        whitespace = request.get_form_var('w', '0')
        if whitespace.isdigit() and int(whitespace) == 1:
            ignore_space = True
        else:
            ignore_space = False
        try:
            commit = project.repo.get_commit(sha1)
            # get_diff 默认与 parent diff
            diff = project.repo.get_diff(ref=sha1,
                                         ignore_space=ignore_space,
                                         rename_detection=True,
                                         linecomments=linecomments,
                                         paths=[path] if path else None)
            if not commit:
                raise TraversalError("not a valid commit ref")
        except IOError:
            raise TraversalError()

        return st('commit.html', **locals())
