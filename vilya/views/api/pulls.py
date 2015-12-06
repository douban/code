# -*- coding: utf-8 -*-

import logging
import warnings

from quixote.errors import TraversalError

from vilya.models.project import CodeDoubanProject
from vilya.models.pull import PullRequest, merge_pull, close_pull
from vilya.models.ticket import Ticket, TicketComment, TicketCommits
from vilya.libs.api_errors import (
    UnauthorizedError, NoPushPermissionError,
    MissingFieldError, InvalidFieldError)

from vilya.views.api.utils import jsonize, json_body
from vilya.views.api.diff import PullDiffMixin

# TODO: 把 diff 相关的拆出来，其实都没必要拿 ticket、pullreq 对象，直接从 project.repo 就行？
# pullreq 那一层wrap反而增加了复用的难度？
# 之后把 compare、pull/new 的 diff 问题解决


class SinglePullUI(PullDiffMixin):
    _q_exports = ['commits', 'comments', 'fulltext', 'moreline',
                  'toggle_whitespace', 'merge', 'close']

    def __init__(self, request, proj_name, ticket_id):
        self.proj_name = proj_name
        self.ticket_id = ticket_id
        self.project = CodeDoubanProject.get_by_name(self.proj_name)
        if not self.project:
            raise TraversalError()
        self.ticket = Ticket.get_by_projectid_and_ticketnumber(
            self.project.id, self.ticket_id)
        if not self.ticket:
            raise TraversalError()

    def __call__(self, request):
        return self._index(request)

    @json_body
    def _q_index(self, request):
        if not self.ticket:
            raise TraversalError()
        action = request.data.get('action')
        if request.method == 'PATCH':
            if action == 'merge':
                return self.merge(request)
            elif action == 'close':
                return self.close(request)
            elif action == 'comment':
                return self.add_comment(request)
            elif action:
                raise InvalidFieldError('action')
            else:
                raise MissingFieldError('action')
        else:
            return self._index(request)

    @jsonize
    def _index(self, request):
        project = self.project
        whitespace = request.get_form_var('whitespace', 'on')
        is_diff = request.get_form_var('diff')
        ignore = False if whitespace == 'on' else True
        pr = PullRequest.get_by_proj_and_ticket(
            self.project.id, self.ticket.ticket_number)
        pr_dict = pr.as_dict()
        if is_diff:
            diff = pr.get_diff(ignore_space=ignore, rename_detection=True)
            raw_diff = diff.raw_diff
            try:
                del raw_diff['diff']
            except KeyError:
                pass
            pr_dict['diff'] = raw_diff
        if request.user:
            pr_dict['can_push'] = project.has_push_perm(request.user.name)
        return pr_dict

    @jsonize
    def commits(self, request):
        if not self.ticket:
            raise TraversalError()

        pr = PullRequest.get_by_proj_and_ticket(
            self.project.id, self.ticket.ticket_number)
        commits = pr.get_commits_shas()
        commits = [TicketCommits.commit_as_dict(self.project, c)
                   for c in commits]
        # commits = reduce(lambda x, y: x + y, commits)
        return commits

    @jsonize
    def add_qaci_comment(self, request):
        content = request.get_form_var('content')
        comment = self.ticket.add_comment(content, 'qaci')
        request.response.set_status(201)
        return comment.as_dict()

    @jsonize
    def comments(self, request):
        if request.method == 'POST':
            return self.add_qaci_comment(request)
        comments = TicketComment.gets_by_ticketid(self.ticket.id)
        cl = []
        for c in comments:
            cl.append(c.as_dict())

        return cl

    @jsonize
    def add_comment(self, request):
        user = request.user
        content = request.data.get('content')
        if not user:
            raise UnauthorizedError
        elif not content:
            raise MissingFieldError('content')
        self.ticket.add_comment(content, user.name)

    @jsonize
    def merge(self, request):
        user = request.user
        if user:
            pullreq = PullRequest.get_by_proj_and_ticket(
                self.project.id,
                self.ticket.ticket_number)
            if pullreq.merged:
                return {'ok': True}
            error = merge_pull(self.ticket, pullreq, user, '', request)
            if error:
                raise NoPushPermissionError(error)
            else:
                return {'ok': True}
        raise UnauthorizedError

    @jsonize
    def close(self, request):
        user = request.user
        if user:
            ticket = self.ticket
            pullreq = PullRequest.get_by_proj_and_ticket(
                self.project.id,
                self.ticket.ticket_number)
            comment = ticket.add_comment('close pr', user.name)
            error = close_pull(self.ticket, pullreq, user, 'close pr',
                               comment, request)
            if error:
                raise NoPushPermissionError(error)
            return {'ok': True}
        raise UnauthorizedError


class PullsUI:
    _q_exports = []

    def __init__(self, request, proj_name):
        self.proj_name = proj_name

    @jsonize
    def _index(self, request):
        project = CodeDoubanProject.get_by_name(self.proj_name)
        open_tickets = Ticket.gets_by_proj(project.id, limit=9999)

        pr_list = []
        for t in open_tickets:
            pullreq = PullRequest.get_by_proj_and_ticket(project.id,
                                                         t.ticket_number)
            if pullreq:
                pr_list.append(pullreq.as_dict())
        return pr_list

    def _q_lookup(self, request, ticket_id):
        return SinglePullUI(request, self.proj_name, ticket_id)

    def _q_index(self, request):
        return self._index(request)

    def __call__(self, request):
        return self._index(request)


class MyPullsUI(object):

    _q_exports = []

    def __init__(self, request):
        self.user = request.user
        if not self.user:
            raise TraversalError()

    @jsonize
    def _index(self, request):
        user = self.user
        yours = user.get_user_submit_pull_requests()
        participated = user.get_participated_pull_requests()
        invited = user.get_invited_pull_requests()

        yours_list = [PullRequest.get_by_ticket(ticket).as_dict()
                      for ticket in yours]
        participated_list = [PullRequest.get_by_ticket(ticket).as_dict()
                             for ticket in participated]
        invited_list = [PullRequest.get_by_ticket(ticket).as_dict()
                        for ticket in invited]

        yours_list = filter(lambda t: t, yours_list)
        participated = filter(lambda t: t, participated)
        invited_list = filter(lambda t: t, invited_list)

        rs = []
        if yours_list:
            rs.append({'section': 'Yours', 'pulls': yours_list})
        if participated_list:
            rs.append({'section': 'Participated', 'pulls': participated_list})
        if invited_list:
            rs.append({'section': 'Invited', 'pulls': invited_list})

        return rs

    def _q_index(self, request):
        return self._index(request)

    def __call__(self, request):
        return self._index(request)


class PullUI(object):
    _q_exports = []

    def __init__(self, request, project_name):
        self.proj_name = project_name

    def _q_lookup(self, request, ticket_id):
        warnings.warn('PullUI is deprecated', DeprecationWarning)
        logging.warning('PullUI is deprecated')
        return SinglePullUI(request, self.proj_name, ticket_id)
