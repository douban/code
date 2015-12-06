# -*- coding: utf-8 -*-

from __future__ import absolute_import
from quixote.errors import TraversalError

from vilya.libs.template import st
from vilya.models.ticket import TicketComment
from vilya.models.project import CodeDoubanProject
from vilya.views.util import jsonize, http_method

_q_exports = []


class PrCommentUI(object):

    _q_exports = ['delete', 'edit']

    def __init__(self, proj_name):
        self.proj_name = proj_name
        self.pr_comment = None

    def _q_lookup(self, request, comment_id):
        comment = TicketComment.get(id=comment_id)
        if not comment:
            raise TraversalError(
                "Unable to find pr_comment %s" % comment_id)
        else:
            self.pr_comment = comment
            return self

    @jsonize
    def delete(self, request):
        user = request.user
        if self.pr_comment.author == user.name:
            ok = self.pr_comment.delete()
            if ok:
                return {'r': 1}  # FIXME: 这里 r=1 表示成功，跟其他地方不统一
        return {'r': 0}

    @jsonize
    @http_method(methods=['POST'])
    def edit(self, request):
        user = request.user
        current_user = request.user
        project = CodeDoubanProject.get_by_name(self.proj_name)
        content = request.get_form_var(
            'pull_request_comment', '').decode('utf-8')
        if self.pr_comment.author == user.name:
            self.pr_comment.update(content)
            comment = TicketComment.get(id=self.pr_comment.id)
            author = user
            return dict(r=0, html=st('/pull/ticket_comment.html', **locals()))
        return {'r': 1}
