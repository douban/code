#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dispatches.notifications.issue import Dispatcher as IssueDispatcher
from vilya.libs.mailer import Mail, MailContext
from vilya.libs.irc import IrcMsg
from vilya.models.actions.issue_comment import IssueComment

EMAIL_TITLE = "RE: [%s] %s (#%s)"
IN_REPLY_TO = '<%s-issue-%s@code>'


class Dispatcher(IssueDispatcher):
    def __init__(self, data):
        IssueDispatcher.__init__(self, data)
        self._comment = data.get('comment')
        self._comment_id = self._comment.id
        self._url = "%s#comment-%s" % (self._issue.url, self._comment.number)

    @property
    def msgs(self):
        return [self.noti, self.mail, self.ircmsg]

    @property
    def noti_data(self):
        action = IssueComment(self._sender, self.now(), self._target,
                              self._issue, self._content)
        return action.to_dict()

    @property
    def ircmsg(self):
        sender = self._sender
        issue = self._issue
        url = self.domain(self._url)
        msg = "%s commented on '%s' ( %s )" % (sender, issue.title, url)
        return IrcMsg(self.irc_receivers, msg)

    @property
    def mail(self):
        sender = self._sender
        content = self._content
        issue = self._issue
        comment = self._comment
        target = self._target

        subject = EMAIL_TITLE % (target, issue.title, issue.number)
        hook_url = self.hook_url
        url = self.domain(self._url)

        toaddr = Mail.addrs_by_usernames([sender])
        ccaddr = Mail.addrs_by_usernames(self.noti_receivers, target)

        in_reply_to = IN_REPLY_TO % (target.name, self._issue_id)
        fromaddr = Mail.customize_sender(sender, target.name)
        status_line = "{} commented on issue [{} (#{})]({})".format(
            sender, issue.title, issue.number, url)

        return Mail(
            subject,
            to=toaddr,
            cc=ccaddr,
            from_=fromaddr,
            in_reply_to=in_reply_to,
            context=MailContext('_', data=locals()))
