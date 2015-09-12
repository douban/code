# -*- coding: utf-8 -*-
from vilya.libs import api_errors

from vilya.models.issue_comment import IssueComment
from vilya.models.gist_comment import GistComment
from vilya.views.api.utils import RestAPIUI


class CommentsUI(RestAPIUI):
    _q_exports = []
    _q_methods = ['get', 'post']

    def __init__(self, request, item):
        if not item:
            raise api_errors.NotFoundError
        self.item = item

    def get(self, request):
        return [c.as_dict() for c in self.item.comments]

    def post(self, request):
        content = request.data.get("content", "")
        if content:
            comment = self.comment_cls.add(
                self.item_id,
                content,
                request.user.name
            )
            return comment.as_dict()
        else:
            raise api_errors.MissingFieldError('content')

    @property
    def item_id(self):
        raise NotImplemented


class IssueCommentsUI(CommentsUI):
    comment_cls = IssueComment

    @property
    def item_id(self):
        return self.item.issue_id

    def _q_lookup(self, request, number):
        comment = self.comment_cls.get_by_issue_id_and_number(
            self.item.issue_id, number)
        return CommentUI(request, comment)


class GistCommentsUI(CommentsUI):
    comment_cls = GistComment

    @property
    def item_id(self):
        return self.item.id

    def _q_lookup(self, request, number):
        comment = self.comment_cls.get(number)
        return CommentUI(request, comment)


class CommentUI(RestAPIUI):
    _q_exports = []
    _q_methods = ['get', 'patch', 'delete']

    def __init__(self, request, comment):
        if not comment:
            raise api_errors.NotFoundError
        self.comment = comment

    def get(self, request):
        return self.comment.as_dict()

    def delete(self, request):
        if request.user.username != self.comment.author_id:
            raise api_errors.NotTheAuthorError('comment', 'delete')
        self.comment.delete()

    def patch(self, request):
        if request.user.username != self.comment.author_id:
            raise api_errors.NotTheAuthorError('comment', 'edit')
        content = request.data.get("content", "")
        if content:
            comment = self.comment
            comment.update(content)
            return comment.as_dict()
        else:
            raise api_errors.MissingFieldError('content')
