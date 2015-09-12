#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dispatches.notifications import NotificationDispatcher
from vilya.libs.irc import IrcMsg
from vilya.libs.mailer import Mail, MailContext
from vilya.models.mute import Mute

IRC_TEMPLATE = "[{state}]Pull request '{title}' #{ticket_id} {ticket_url} \
    build #{qaci_id} {qaci_url} {qaci_sha} of {project_name}."
EMAIL_TITLE_TEMPLATE = "[{state}] {project_name}#{qaci_id} ({qaci_sha})"


class Dispatcher(NotificationDispatcher):

    def __init__(self, data):
        NotificationDispatcher.__init__(self, data)
        self._sha = data.get('sha')
        self._project = data.get('project')
        self._state = data.get('state')
        self._pull = data.get('pull')
        self._qaci_url = data.get('url')
        self._ticket = self._pull.ticket
        self._target = self._pull.to_proj
        url = self._qaci_url
        if url.endswith('/'):
            url = url[:-1]
        self.build_number = url.rpartition('/')[-1]

    @property
    def msgs(self):
        return [self.ircmsg]

    @property
    @NotificationDispatcher.save_as_attr
    def noti_receivers(self):
        participants = self._ticket.participants
        extra = [self._ticket.author, self._pull.to_proj.owner_id]
        receivers = set(participants + extra)
        return Mute.filter('ticket',
                           self._target.name,
                           self._pull.ticket_id,
                           receivers)

    @property
    def irc_receivers(self):
        return IrcMsg.irc_receiver_filter(self.noti_receivers, self._target)

    @property
    def mail_receivers(self):
        toaddr = Mail.addrs_by_usernames([self._ticket.author])
        #ccaddr = Mail.addrs_by_usernames(self.noti_receivers)
        ccaddr = []
        return toaddr, ccaddr

    @property
    def ircmsg(self):
        sha = self._sha
        state = self._state
        pull = self._pull
        ticket_id = self._ticket.ticket_id
        title = self._ticket.title
        number = self.build_number
        url = self._qaci_url
        project = pull.to_proj
        qaci_url = "( %s ) " % url if state == 'failure' else ''
        msg = IRC_TEMPLATE.format(state=state,
                                  title=title,
                                  ticket_id=ticket_id,
                                  ticket_url="( %s )" % pull.full_url,
                                  qaci_id=number,
                                  qaci_url=qaci_url,
                                  qaci_sha=sha[:8],
                                  project_name=project.name)
        return IrcMsg(self.irc_receivers, msg)

    @property
    def mail(self):
        sha = self._sha
        state = self._state
        pull = self._pull
        url = self._qaci_url
        project = pull.to_proj
        number = self.build_number
        commit = project.repo.get_commit(sha)
        ticket_url = pull.full_url
        subject = EMAIL_TITLE_TEMPLATE.format(state=state,
                                              project_name=project.name,
                                              qaci_id=number,
                                              qaci_sha=sha[:8])
        toaddr, ccaddr = self.mail_receivers
        in_reply_to = None
        message_id = None
        return Mail(subject,
                    to=toaddr,
                    cc=ccaddr,
                    in_reply_to=in_reply_to,
                    message_id=message_id,
                    context=MailContext('qaci', data=locals()))
