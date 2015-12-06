#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dispatches.notifications import NotificationDispatcher
from vilya.libs.text import get_mentions_from_text
from vilya.models.actions.pull_comment import PullComment
from vilya.models.pull import PullRequest
from vilya.models.ticket import TicketComment
from vilya.models.notification import Notification
from vilya.models.mute import Mute
from vilya.libs.irc import IrcMsg
from vilya.libs.mailer import Mail, MailContext


EMAIL_TITLE = '[%s] %s (#%s)'  # [project name] pull request title (#ticket id)
EMAIL_IN_REPLY_TO = '<%s-pull-%s@code>'
EMAIL_REPLY_BOT = 'code-email-reply+code@dappsmail.douban.com'


class Dispatcher(NotificationDispatcher):
    def __init__(self, data):
        NotificationDispatcher.__init__(self, data)
        self._sender = data.get('sender')
        self._comment = data.get('comment')
        self._content = self._comment.content if self._comment else data.get('content', '')
        self._ticket = data.get('ticket')
        self._pullreq = PullRequest.get_by_ticket(self._ticket)
        self._target = self._pullreq.to_proj
        self._is_ticketcomment = isinstance(self._comment, TicketComment)

    @property
    def msgs(self):
        return [self.ircmsg, self.mail, self.noti]

    @property
    def uid(self):
        if self._comment:
            return self._comment.uid
        else:
            return self._uid

    @property
    @NotificationDispatcher.save_as_attr
    def noti_receivers(self):
        participants = self._ticket.participants
        mentions = get_mentions_from_text(self._content)
        extra = [self._ticket.author, self._pullreq.to_proj.owner_id]
        receivers = set(participants + mentions + extra)
        receivers.discard(self._sender)
        return Mute.filter('ticket', self._target.name,
                           self._pullreq.ticket_id, receivers)

    @property
    @NotificationDispatcher.save_as_attr
    def noti_data(self):
        pullreq = self._pullreq
        ticket = self._ticket
        uid = self.uid
        sender = self._sender
        content = self._content
        url = self.domain("/%s/pull/%s/#%s" % (pullreq.to_proj,
                                               ticket.ticket_id,
                                               uid))
        # TODO: 我认为数据应该都放在action里，这里只负责dispatch，而涉及到复杂逻辑计算的都应该合到相应的model里，
        # 但是这部分还在重构，会有交集，不便修改
        action = PullComment(sender, self.now(), pullreq, ticket,
                             content, url)
        return action.to_dict()

    @property
    def noti(self):
        return Notification(self.uid, self.noti_receivers, self.noti_data)

    @property
    def irc_receivers(self):
        return IrcMsg.irc_receiver_filter(self.noti_receivers, self._target)

    @property
    def ircmsg(self):
        data = self.noti_data
        url = data.get('url')
        proj = data.get('proj')
        sender = self._sender
        message = "%s commented on %s %s" % (sender, proj, url)
        return IrcMsg(self.irc_receivers, message)

    @property
    def mail_receivers(self):
        toaddr = Mail.addrs_by_usernames([self._ticket.author])
        ccaddr = Mail.addrs_by_usernames(self.noti_receivers)
        toaddr.add(EMAIL_REPLY_BOT)
        return toaddr, ccaddr

    @property
    def mail_subject(self):
        proj = self._pullreq.to_proj
        ticket = self._ticket
        ticket_id = ticket.ticket_id
        ticket_title = ticket.title
        return EMAIL_TITLE % (proj.name, ticket_title, ticket_id)

    @property
    def reply_mail_subject(self):
        return "RE:" + self.mail_subject

    @property
    def in_reply_to(self):
        proj = self._pullreq.to_proj
        ticket = self._ticket
        ticket_id = ticket.ticket_id
        return EMAIL_IN_REPLY_TO % (proj.name, ticket_id)

    @property
    def mail(self):
        comment = self._comment
        uid = self.uid

        ticket = self._ticket
        ticket_id = ticket.ticket_id
        ticket_title = ticket.title

        author = self._sender
        content = self._content

        pullreq = self._pullreq
        proj = pullreq.to_proj
        proj_url = self.domain(proj.url)
        proj_name = proj.name

        if self._is_ticketcomment:
            pr_url = '/%s/pull/%s/' % (proj_name, ticket_id)
            url = self.domain('%s#%s' % (pr_url, uid))
        else:
            path = comment.path
            url = self.domain(str('/%s/pull/%s/files#%s' % (proj_name,
                                                            ticket_id,
                                                            uid)))
            # FIXME: move to pullreq.xx
            diff = pullreq.get_diff(ref=comment.from_sha, paths=[path])
            # FIXME: new smart_slice
            #diff_content = diff.patches[0].smart_slice(comment.position) if diff and diff.patches else []
            diff_content = ''

        subject = self.reply_mail_subject
        in_reply_to = self.in_reply_to
        hook_url = self.hook_url
        fromaddr = Mail.customize_sender(author, proj_name)
        toaddr, ccaddr = self.mail_receivers
        return Mail(subject,
                    to=toaddr,
                    cc=ccaddr,
                    from_=fromaddr,
                    in_reply_to=in_reply_to,
                    context=MailContext('codereview', data=locals()))
