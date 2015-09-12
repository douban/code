#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dispatches.notifications import NotificationDispatcher
from vilya.libs.mailer import Mail, MailContext
from vilya.libs.irc import IrcMsg
from vilya.libs.text import get_mentions_from_text
from vilya.models.actions.issue import Issue as IssueAciton
from vilya.models.notification import Notification

EMAIL_TITLE = '[%s] %s (#%s)'  # [project name] issue title (#issue id)
IN_REPLY_TO = '<%s-issue-%s@code>'


class Dispatcher(NotificationDispatcher):
    def __init__(self, data):
        NotificationDispatcher.__init__(self, data)
        self._sender = data.get('sender')
        self._content = data.get('content')
        self._issue = data.get('issue')
        self._issue_id = self._issue.issue_id
        self._target = self._issue.target

    @property
    def msgs(self):
        return [self.noti, self.ircmsg, self.mail]

    @property
    @NotificationDispatcher.save_as_attr
    def noti_receivers(self):
        issue = self._issue
        target = self._target
        mentions = get_mentions_from_text(self._content)
        participants = [p.user_id for p in issue.participants if p]
        if issue.target_type == 'project':
            extra_receivers = [issue.creator_id, target.owner_id]
        else:
            extra_receivers = self._target.user_ids
            extra_receivers.append(issue.creator_id)
        rs = set(mentions + participants + extra_receivers)
        rs.discard(self._sender)
        return rs

    @property
    @NotificationDispatcher.save_as_attr
    def noti_data(self):
        content = self._content
        issue = self._issue
        target = self._target
        sender = self._sender
        state = 'closed' if issue.closer_id else 'open'
        action = IssueAciton(sender, self.now(), target, issue, state, content)
        return action.to_dict()

    @property
    def noti(self):
        return Notification(self._uid, self.noti_receivers, self.noti_data)

    @property
    def irc_receivers(self):
        return IrcMsg.irc_receiver_filter(self.noti_receivers, self._target)

    @property
    def ircmsg(self):
        sender = self._sender
        issue = self._issue
        target = self._target
        url = self.domain(issue.url)
        action = 'closed' if issue.closer_id else "opened"
        msg = "Issue '%s' ( %s ) of %s is %s by %s" % (
            issue.title, url, target.name, action, sender)
        return IrcMsg(self.irc_receivers, msg)

    @property
    def mail(self):
        sender = self._sender
        content = self._content
        issue = self._issue
        target = self._target
        url = self.domain(issue.url)
        toaddrs = Mail.addrs_by_usernames(self.noti_receivers, target)
        fromaddr = Mail.customize_sender(sender, target.name)
        hook_url = self.hook_url
        in_reply_to = IN_REPLY_TO % (target.name, self._issue_id)
        if issue.is_closed:
            status_line = "Issue closed by %s" % sender
            subject = EMAIL_TITLE % (target.name, issue.title, issue.number)
            message_id = None
        else:
            status_line = "%s create a new issue [%s (#%s)](%s)" % (
                sender, issue.title, issue.number, url)
            subject = "RE:" + EMAIL_TITLE % (target.name, issue.title, issue.number)
            message_id = in_reply_to
        if toaddrs:
            return Mail(subject,
                        to=toaddrs,
                        from_=fromaddr,
                        in_reply_to=in_reply_to,
                        message_id=message_id,
                        context=MailContext('_', data=locals()))
