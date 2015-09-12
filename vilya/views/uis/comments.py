# -*- coding: utf-8 -*-

from __future__ import absolute_import

from quixote.errors import TraversalError

from vilya.models.project import CodeDoubanProject
from vilya.models.comment import Comment, latest
from vilya.views.util import http_method

_q_exports = []


class CommentUI:
    ''' project commit comment ui '''
    _q_exports = ['new']

    def __init__(self, proj_name):
        self.proj_name = proj_name

    def _q_index(self, request):
        return "Last comments list TODO" + str(latest())

    @http_method(methods=['POST'])
    def new(self, request):
        project = CodeDoubanProject.get_by_name(self.proj_name)
        user = request.user
        ref = request.get_form_var('ref')
        assert ref, "comment ref cannot be empty"
        content = request.get_form_var('content', '')
        new_comment = Comment.add(project, ref, user.name, content)

        return request.redirect("/%s/commit/%s#%s" %
                                (self.proj_name, ref, new_comment.uid))

    def _q_lookup(self, request, comment_id):
        if request.method == 'DELETE':
            # FIXME: 不用验证user？
            ok = Comment.delete(comment_id)
            if not ok:
                raise TraversalError(
                    "Unable to delete comment %s" % comment_id)
            return ''
        return "Display comment %s TODO" % comment_id
