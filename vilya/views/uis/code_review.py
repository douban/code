# -*- coding: utf-8 -*-

from __future__ import absolute_import
from quixote.errors import TraversalError

from vilya.views.util import jsonize, http_method
from vilya.models.linecomment import PullLineComment
from vilya.models.project import CodeDoubanProject
from vilya.libs.template import st

_q_exports = []


class CodeReviewUI(object):

    _q_exports = ['delete', 'edit']

    def __init__(self, proj_name):
        self.proj_name = proj_name
        self.code_review = None

    def _q_lookup(self, request, comment_id):
        comment = PullLineComment.get(comment_id)
        if not comment:
            raise TraversalError(
                "Unable to find comment %s" % comment_id)
        else:
            self.code_review = comment
            return self

    @jsonize
    def delete(self, request):
        user = request.user
        if self.code_review.author == user.name:
            ok = self.code_review.delete()
            if ok:
                return {'r': 1}  # FIXME: 这里 r=1 表示成功，跟其他地方不统一
        return {'r': 0}

    @jsonize
    @http_method(methods=['POST'])
    def edit(self, request):
        user = request.user
        project = CodeDoubanProject.get_by_name(self.proj_name)
        content = request.get_form_var(
            'pull_request_review_comment', '').decode('utf-8')
        if self.code_review.author == user.name:
            self.code_review.update(content)
            linecomment = PullLineComment.get(self.code_review.id)
            pullreq = True
            return dict(
                r=0, html=st('/pull/ticket_linecomment.html', **locals()))
        return dict(r=1)
