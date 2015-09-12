#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dispatches.notifications.codereview import Dispatcher as CodeReviewDispatcher
from vilya.libs.mailer import Mail, MailContext
from vilya.libs.irc import IrcMsg
from vilya.models.actions.pull import Pull as PullAction


class Dispatcher(CodeReviewDispatcher):
    def __init__(self, data):
        CodeReviewDispatcher.__init__(self, data)
        self._status = data.get('status')
        self._newversion = data.get('new_version')
        self._extra_receivers = data.get('extra_receivers')

    @property
    def msgs(self):
        return [self.noti, self.ircmsg, self.mail]

    @property
    @CodeReviewDispatcher.save_as_attr
    def noti_data(self):
        pullreq = self._pullreq
        ticket = self._ticket
        state = self._status
        new_version = self._newversion
        pullreq_url = "/%s/pull/%s/" % (pullreq.to_proj,
                                        ticket.ticket_id)
        # TODO: 这种逻辑塞到 model.pull 里更好点?
        if new_version:
            owner = pullreq.merge_by or self._sender
        else:
            owner = ticket.owner.name
        commiter = ticket.author
        action = PullAction(commiter, self.now(), pullreq, ticket,
                            owner, state, pullreq_url)
        return action.to_dict()

    @property
    def ircmsg(self):
        data = self.noti_data
        title = data.get('title')
        url = self.domain(data.get('url'))
        to_proj = data.get('to_proj')
        sender = self._sender
        status = self._status
        sta = 'posted' if status == 'unmerge' else status
        message = "Pull request '%s' ( %s ) of %s is %s by %s" % (
            title, url, to_proj, sta, sender)
        return IrcMsg(self.irc_receivers, message)

    @property
    def extra_receivers(self):
        if self._extra_receivers:
            return Mail.addrs_by_usernames(self._extra_receivers)
        else:
            return set()

    @property
    def mail(self):
        comment = self._comment
        pullreq = self._pullreq
        to_proj = pullreq.to_proj
        ticket = self._ticket
        ticket_id = ticket.ticket_id
        status = self._status
        sender = self._sender
        diffurl = self.domain('/%s/pull/%s' % (to_proj.name, ticket_id))
        url = "%s/" % diffurl
        hook_url = self.hook_url

        if status == 'unmerge':
            _, toaddr = self.mail_receivers
            ccaddr = self.extra_receivers
            subject = self.mail_subject
            content = self._content
            message_id = self.in_reply_to
        else:
            toaddr, ccaddr = self.mail_receivers
            subject = self.reply_mail_subject
            content = """Pull request [{ticket_title} (#{ticket_id})]({url}) is {status} by {sender} """.format(
                ticket_title=ticket.title,
                ticket_id=ticket_id,
                url=url,
                status=status,
                sender=sender)
            message_id = None

        in_reply_to = self.in_reply_to
        fromaddr = Mail.customize_sender(self._sender, to_proj.name)
        return Mail(subject,
                    to=toaddr,
                    cc=ccaddr,
                    from_=fromaddr,
                    in_reply_to=in_reply_to,
                    message_id=message_id,
                    context=MailContext('pullrequest', data=locals()))
