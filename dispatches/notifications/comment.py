#!/usr/bin/env python
# -*- coding: utf-8 -*-

from vilya.config import DOMAIN
from vilya.libs.irc import IrcMsg
from vilya.libs.text import get_mentions_from_text
from vilya.libs.mailer import Mail, MailContext
from dispatches.notifications import NotificationDispatcher
from vilya.models.actions.commit_comment import CommitComment
from vilya.models.feed import FeedMsg
from vilya.models.project import CodeDoubanProject
from vilya.models.notification import Notification

EMAIL_TITLE = '[%s] %s'  # [project name] commit sha
EMAIL_IN_REPLY_TO = '<%s-commit-%s@code>'
EMAIL_REPLY_BOT = 'code-email-reply+code@dappsmail.douban.com'


class Dispatcher(NotificationDispatcher):
    def __init__(self, data):
        NotificationDispatcher.__init__(self, data)
        self._comment = data.get('comment')
        # TODO: get commit author by sha # ...现在应该是 None
        self._commit_author = data.get('commit_author')
        self._is_line_comment = data.get('is_line_comment')  # no use
        self._proj = CodeDoubanProject.get(self._comment.project_id)

    @property
    def msgs(self):
        return [self.noti, self.ircmsg, self.feedmsg, self.mail]

    @property
    def uid(self):
        return self._comment.uid

    @property
    def full_url(self):
        proj = self._proj
        comment = self._comment
        url = '%s/%s/commit/%s#%s' % (DOMAIN, proj.name, comment.ref, self.uid)
        return url

    @property
    def noti_receivers(self):
        comment = self._comment
        comments = comment.gets_by_proj_and_ref(
            self._proj.id,
            comment.ref)
        co_authors = {c.author for c in comments}
        mentions = set(get_mentions_from_text(comment.content))
        extra_receivers = set([r for r in (self._proj.owner_id, self._commit_author) if r])
        rs = (co_authors | mentions | extra_receivers)
        rs.discard(comment.author)
        return rs

    @property
    def noti_data(self):
        comment = self._comment
        proj = self._proj
        url = '/%s/commit/%s#%s' % (proj.name, comment.ref, self.uid)
        action = CommitComment(comment.author, comment.created, proj.name,
                               comment.ref, comment.content, url)
        return action.to_dict()

    @property
    def noti(self):
        return Notification(self.uid, self.noti_receivers, self.noti_data)

    @property
    def irc_receivers(self):
        return IrcMsg.irc_receiver_filter(self.noti_receivers, self._proj)

    @property
    def ircmsg(self):
        comment = self._comment
        url = self.full_url
        msg = "%s commented on commit '%s' ( %s )" % (
            comment.author,
            comment.ref[:8],
            url)
        return IrcMsg(self.irc_receivers, msg)

    @property
    def feedmsg(self):
        sender = self._comment.author
        return FeedMsg(sender, [], project=self._proj, data=self.noti_data)

    @property
    def mail_receivers(self):
        toaddr = Mail.addrs_by_usernames([self._proj.owner_id])
        ccaddr = Mail.addrs_by_usernames(self.noti_receivers)
        toaddr.add(EMAIL_REPLY_BOT)
        return toaddr, ccaddr

    @property
    def mail_subject(self):
        proj = self._proj
        comment = self._comment
        title = comment.ref
        return EMAIL_TITLE % (proj.name, title)

    @property
    def reply_mail_subject(self):
        return "RE:" + self.mail_subject

    @property
    def in_reply_to(self):
        proj = self._proj
        comment = self._comment
        title = comment.ref
        return EMAIL_IN_REPLY_TO % (proj.name, title)

    @property
    def mail(self):
        proj = self._proj
        comment = self._comment
        in_reply_to = self.in_reply_to
        subject = self.reply_mail_subject
        url = self.full_url
        hook_url = self.hook_url
        content = self._comment.content
        author = comment.author
        proj_name = proj.name
        fromaddr = Mail.customize_sender(author, proj_name)
        toaddr, ccaddr = self.mail_receivers
        return Mail(subject,
                    to=toaddr,
                    cc=ccaddr,
                    from_=fromaddr,
                    in_reply_to=in_reply_to,
                    context=MailContext('codereview', data=locals()))
