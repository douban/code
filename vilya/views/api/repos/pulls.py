# -*- coding: utf-8 -*-

from vilya.libs import api_errors
from vilya.libs.text import get_mentions_from_text
from vilya.models.project import CodeDoubanProject
from vilya.models.pull import PullRequest, add_pull, merge_pull, close_pull
from vilya.models.ticket import Ticket
from vilya.models.consts import LINECOMMENT_INDEX_EMPTY
from vilya.models.user import User
from vilya.views.api.utils import RestAPIUI, jsonize
from vilya.libs.api_errors import (
    InvalidFieldError, NoPushPermissionError,
    MissingFieldError, NotJSONError, NotFoundError)


class PullUI(RestAPIUI):
    _q_exports = ['files']
    _q_methods = ['get', 'patch']

    def __init__(self, project_id, ticket_id):
        self.project_id = project_id
        self.ticket_id = ticket_id

        self.ticket = Ticket.get_by_projectid_and_ticketnumber(self.project_id,
                                                               self.ticket_id)

        if not self.ticket:
            raise NotFoundError('pull')

        self.pullreq = PullRequest.get_by_proj_and_ticket(
            self.project_id, self.ticket.ticket_number)

    def get(self, request):
        return self.pullreq.as_dict()

    def patch(self, request):
        request.data = request.data or request.form
        action = request.data.get('action')
        if action == 'merge':
            return self.merge(request)
        elif action == 'close':
            return self.close(request)
        elif action == 'comment':
            return self.add_comment(request)
        elif action == 'codereview':
            return self.add_codereview(request)
        elif action:
            raise InvalidFieldError('action')
        else:
            raise MissingFieldError('action')

    def merge(self, request):
        user = request.user
        ticket = self.ticket
        pullreq = self.pullreq
        if pullreq.merged:
            return {'ok': True}
        error = merge_pull(ticket, pullreq, user, '', request)
        if error:
            raise NoPushPermissionError(error)
        return {'ok': True}

    def close(self, request):
        user = request.user
        ticket = self.ticket
        pullreq = self.pullreq
        comment = ticket.add_comment('close pr', user.name)
        error = close_pull(ticket, pullreq, user, 'close pr', comment, request)
        if error:
            raise NoPushPermissionError(error)
        return {'ok': True}

    def add_comment(self, request):
        user = request.user
        content = request.data.get('content')
        if not content:
            raise MissingFieldError('content')
        comment = self.ticket.add_comment(content, user.name)
        return comment.as_dict()

    def add_codereview(self, request):
        content = request.data.get('content')
        from_sha = request.data.get('from_sha')
        to_sha = request.data.get('to_sha')
        old_path = request.data.get('old_path')
        new_path = request.data.get('new_path')
        from_oid = request.data.get('from_oid')
        to_oid = request.data.get('to_oid')
        new_no = request.data.get('new_no')
        old_no = request.data.get('old_no', '')

        for t in ('content', 'from_sha', 'old_path', 'new_path', 'from_oid',
                  'to_oid', 'new_no'):
            val = locals()[t]
            if not val.strip():
                raise MissingFieldError(t)
        old_no = int(old_no) if old_no.isdigit() else LINECOMMENT_INDEX_EMPTY
        new_no = int(new_no) if new_no.isdigit() else LINECOMMENT_INDEX_EMPTY

        author = request.data.get('username')
        if not author:
            author = request.user.name
        self.ticket.add_codereview(from_sha, to_sha, old_path, new_path,
                                   from_oid, to_oid, old_no, new_no, author,
                                   content)

        at_users = get_mentions_from_text(content)
        for u in at_users:
            User(u).add_invited_pull_request(self.ticket.id)
        return {'ok': True}

    @jsonize
    def files(self, request):
        whitespace = request.get_form_var('whitespace', 'on')
        ignore = False if whitespace == 'on' else True
        pr = self.pullreq
        diff = pr.get_diff(ignore_space=ignore, rename_detection=True)
        raw_diff = diff.raw_diff
        return [dict(sha=d['new_oid'],
                     filename=d['new_file_path'],
                     deletions=d['deletions'],
                     additions=d['additions'],
                     status=d['status']) for d in raw_diff['patches']]


class PullsUI(RestAPIUI):
    _q_exports = []
    _q_methods = ['get', 'post']

    def __init__(self, repo):
        self.repo = repo

    def get(self, request):
        _date_from = None
        _date_to = None
        state = request.get_form_var('state', '')
        author = request.get_form_var('author', '')
        date_from = request.get_form_var('from', '')
        date_to = request.get_form_var('to', '')
        if not state or state == "open":
            closed = False
        else:
            closed = True
        if date_from:
            _date_from = date_from
        if date_to:
            _date_to = date_to

        tickets = Ticket.gets(project_id=self.repo.id,
                              author=author,
                              date_from=_date_from,
                              date_to=_date_to,
                              closed=closed)
        pulls = []
        for t in tickets:
            pull = PullRequest.get_by_proj_and_ticket(self.repo.id,
                                                      t.ticket_number)
            pulls.append(pull.as_dict())
        return pulls

    def post(self, request):
        """
        title
        body
        to_ref
        from_project
        from_ref
        """
        user = request.user
        if not request.data:
            raise NotJSONError
        data = request.data

        title = data.get('title').decode('utf8')
        body = data.get('body').decode('utf8')
        base_ref = data.get('base_ref')
        head = data.get('head')
        head_repo = data.get('head_repo')

        from_proj = head_repo
        from_ref = head
        to_ref = base_ref
        to_proj = self.repo
        if not all([from_ref, from_proj, to_ref, to_proj, title]):
            # FIXME: more details
            raise api_errors.UnprocessableEntityError

        from_proj = CodeDoubanProject.get_by_name(from_proj)

        if not from_proj.has_push_perm(user.name):
            raise api_errors.NoPushPermissionError

        pullreq = PullRequest.open(from_proj, from_ref, to_proj, to_ref)
        ticket = Ticket(None, None, to_proj.id, title, body, user.username,
                        None,
                        None)
        pullreq = add_pull(ticket, pullreq, user)
        return pullreq.as_dict()

    def _q_lookup(self, request, number):
        return PullUI(self.repo.id, number)
