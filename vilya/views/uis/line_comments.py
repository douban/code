# -*- coding: utf-8 -*-

from __future__ import absolute_import
from quixote.errors import TraversalError

from vilya.libs.template import st
from dispatches import dispatch
from vilya.models.project import CodeDoubanProject
from vilya.models.linecomment import CommitLineComment
from vilya.views.util import http_method, jsonize
from vilya.models.consts import LINECOMMENT_INDEX_EMPTY

_q_exports = []


class LineCommentUI:

    # TODO: edit
    _q_exports = ['create', 'delete']

    def __init__(self, proj_name):
        self.proj_name = proj_name
        self.linecomment = None

    # TODO: 增加前端信息后修改
    @jsonize
    @http_method(methods=['POST'])
    def create(self, request):
        user = request.user
        if not user:
            return dict(r=1)
        project = CodeDoubanProject.get_by_name(self.proj_name)
        project_id = project.id
        from_sha = request.get_form_var('from_sha')
        assert from_sha, "comment from_sha cannot be empty"
        old_path = request.get_form_var('old_path')
        assert old_path, "comment old_path cannot be empty"
        new_path = request.get_form_var('new_path')
        assert new_path, "comment new path cannot be empty"
        # position = request.get_form_var('position')
        # assert position, "comment position cannot be empty"
        from_oid = request.get_form_var('from_oid')
        assert from_oid, "comment from_oid cannot be empty"
        to_oid = request.get_form_var('to_oid')
        assert to_oid, "comment to_oid cannot be empty"
        old = request.get_form_var('old_no')
        old = int(old) if old.isdigit() else LINECOMMENT_INDEX_EMPTY
        new = request.get_form_var('new_no')
        new = int(new) if new.isdigit() else LINECOMMENT_INDEX_EMPTY
        content = request.get_form_var('content', '')
        # FIXME: commit_author is None
        commit_author = request.get_form_var('commit_author')
        if not content.strip():
            return {'error': 'Content is empty!'}

        comment = CommitLineComment.add(project_id, from_sha, '',
                                        old_path, new_path,
                                        from_oid, to_oid,
                                        old, new, user.name, content)

        dispatch('comment', data={
            'comment': comment,
            'commit_author': commit_author,
            'is_line_comment': True,
        })

        # TODO: 目前只是回写一个链接，可以多传点信息支持直接回写到pr linecomment
        # for commit linecomments rewrite to pr
        dispatch('comment_actions', data={
            'type': 'commit_linecomment',
            'comment': comment,
            'commit_author': commit_author,
        })

        comment_uid = comment.uid
        return dict(r=0, html=st('/commit_linecomment.html', **locals()))

    # TODO: jsonize
    def delete(self, request):
        import json
        user = request.user
        comment = self.linecomment
        if comment.author == user.name:
            ok = comment.delete()
            if not ok:
                raise TraversalError(
                    "Unable to delete comment %s" % comment.id)
            return json.dumps({'r': 1})
        return json.dumps({'r': 0})

    def _q_lookup(self, request, comment_id):
        comment = CommitLineComment.get(comment_id)
        if not comment:
            raise TraversalError(
                "Unable to find comment %s" % comment_id)
        else:
            self.linecomment = comment
            return self
