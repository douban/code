#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dispatches.notifications import NotificationDispatcher
from vilya.libs.mailer import Mail, MailContext
from vilya.models.mute import Mute
#from vilya.models.actions.pull_commit import PullCommit  # feed will need

EMAIL_TITLE = "[%s] %s (#%s)"
IN_REPLY_TO = '<%s-pull-%s@code>'
COMMIT_LIMIT = 3


class Dispatcher(NotificationDispatcher):
    def __init__(self, data):
        NotificationDispatcher.__init__(self, data)
        self._deltacommits = data.get('deltacommits')
        self._pullreq = data.get('pullreq')
        self._ticket = data.get('ticket')
        self._sender = self._pullreq.from_proj.owner_name
        self._target = self._pullreq.to_proj

    @property
    def msgs(self):
        return [self.mail]

    @property
    def mail_receivers(self):
        ticket = self._ticket
        ticket_id = ticket.ticket_id
        target = self._target
        to_receivers = Mute.filter('ticket', target.name,
                                   ticket_id, [ticket.author, ])
        cc_recievers = Mute.filter('ticket', target.name,
                                   ticket_id, ticket.participants)
        toaddr = Mail.addrs_by_usernames(to_receivers, target)
        ccaddr = Mail.addrs_by_usernames(cc_recievers, target)
        return toaddr, ccaddr

    @property
    def mail(self):
        ticket = self._ticket
        pullreq = self._pullreq
        target = self._target
        deltacommits = self._deltacommits
        sender = self._sender
        if len(deltacommits) > COMMIT_LIMIT:
            more = self.domain("/%s/compare/%s...%s" % (
                pullreq.to_proj.name,
                deltacommits[-COMMIT_LIMIT-1].sha,
                deltacommits[0].sha,))
            more_count = len(deltacommits) - COMMIT_LIMIT
        delta_commits = [(c.author.name, c.shortlog, self.domain(c.url), c.shortsha)
                         for c in reversed(deltacommits[-COMMIT_LIMIT:])]
        hook_url = self.hook_url
        ticket_url = self.domain(ticket.url)
        in_reply_to = IN_REPLY_TO % (target.name, ticket.ticket_id)
        subject = EMAIL_TITLE % (target.name, ticket.title, ticket.ticket_id)
        fromaddr = Mail.customize_sender(sender, target.name)
        toaddr, ccaddr = self.mail_receivers
        return Mail(subject,
                    to=toaddr,
                    cc=ccaddr,
                    from_=fromaddr,
                    in_reply_to=in_reply_to,
                    context=MailContext('new_commits', data=locals()))
