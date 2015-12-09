# -*- coding: utf-8 -*-

from quixote.errors import TraversalError
from vilya.libs.template import st
from vilya.libs.text import parse_emoji, render_markdown_with_project
from vilya.models.ticket import Ticket
from vilya.models.project import CodeDoubanProject
from vilya.models.pull import PullRequest
from vilya.views.util import jsonize

_q_exports = []


def _q_lookup(request, uid):
    if uid.isdigit():
        ticket = Ticket.get(uid)
        if ticket:
            return TicketUI(ticket)
    raise TraversalError


class TicketUI(object):
    _q_exports = ['edit', ]

    def __init__(self, ticket):
        self.project = CodeDoubanProject.get(ticket.project_id)
        self.proj_name = self.project.name
        self.ticket_id = ticket.ticket_number
        self.ticket = ticket
        self.pullreq = PullRequest.get_by_proj_and_ticket(
            self.project.id, self.ticket_id)

    @jsonize
    def edit(self, request):
        if request.method == 'POST':
            title = request.get_form_var('title', '').decode('utf-8')
            content = request.get_form_var('content', '').decode('utf-8')
            user = request.user
            user = user.name if user else None
            if user == self.ticket.author:
                self.ticket.update(title, content)
                content_html = render_markdown_with_project(
                    content, self.proj_name)
                content_html += st('/widgets/markdown_checklist.html',
                                   **locals())
                return {'r': 0, 'title': title, 'content': content,
                        'title_html': parse_emoji(title), 'content_html': content_html}
        return {'r': 1}
