#!/usr/bin/env python
# encoding: utf-8

import re
import logging
logging.getLogger().setLevel(logging.DEBUG)

from cgi import escape
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart
from email.header import Header

import misaka
from vilya.libs.template import code_templates
from dae.api.mail import send_mail, InvalidEmailAddress
from vilya.libs.mail import send_mail as send_big_mail
from mako.exceptions import TopLevelLookupException
from vilya.models.user import get_author_by_email, User
from vilya.config import (
    DOMAIN, DEFAULT_NOTIFY_SENDER_ADDR,
    CUSTOMIZE_NOTIFY_SENDER_ADDR, TRASH_EMAIL_ADDR)
from vilya.libs.text import RE_USER_MENTION

RE_HTML_TAG = re.compile(r'<[^>]+>')


class _MailHtmlRenderer(misaka.HtmlRenderer):

    def preprocess(self, text):
        r = r'\1 [@\2](%s/people/\2/) ' % DOMAIN
        return RE_USER_MENTION.sub(r, text)

    def codespan(self, code):
        return ' <code style="color:#666;background:#ddd;"> %s </code> ' % code

    def block_code(self, code, language):
        return ('<pre style="color:#666; border-left:solid 2px#ccc;padding-left:2px">'
                '<code>%s</code></pre>') % escape(code.strip())

    def header(self, text, level):
        html = '\n<span style="margin:0;font-weight:bold">{level}</span> {text}\n'
        return html.format(level='#' * level, text=text)

    def image(self, link, title='', alt=''):
        alt = alt or title or link
        return '<a href="{link}">[img:{alt}]</a>'.format(alt=alt,
                                                         link=link)

    def paragraph(self, text):
        return '\n%s\n' % text

    def list(self, contents, ordered):
        return '\n%s\n' % contents

    def list_item(self, line, ordered):
        return '* %s' % line

_html_renderer = _MailHtmlRenderer(misaka.HTML_HARD_WRAP |
                                   misaka.HTML_SAFELINK |
                                   misaka.HTML_SKIP_STYLE |
                                   misaka.HTML_SKIP_SCRIPT |
                                   misaka.HTML_ESCAPE)

_mail_md_renderer = misaka.Markdown(_html_renderer,
                                    extensions=misaka.EXT_FENCED_CODE |
                                    misaka.EXT_NO_INTRA_EMPHASIS |
                                    misaka.EXT_AUTOLINK |
                                    misaka.EXT_TABLES |
                                    misaka.EXT_STRIKETHROUGH)


class MailDirectContext():

    def __init__(self, html, text=''):
        self._html = html
        self._text = text

    def render_html(self):
        return self._html

    def render_text(self):
        return self._text if self._text else RE_HTML_TAG.sub('', self.html)

    @property
    def html(self):
        return self.render_html()

    @property
    def text(self):
        return self.render_text()


class MailContext(MailDirectContext):

    def __init__(self, layout, data=None):
        try:
            self._html_layout = code_templates.get_template(
                '/mailer/{}.html'.format(layout))
        except TopLevelLookupException:
            self._html_layout = code_templates.get_template('/mailer/_.html')

        try:
            self._text_layout = code_templates.get_template(
                '/mailer/{}.text'.format(layout))
        except TopLevelLookupException:
            self._text_layout = code_templates.get_template('/mailer/_.text'.format(layout))

        self.data = data if data else {}
        if 'self' in self.data:
            del self.data['self']
        MailDirectContext.__init__(self, self.html, self.text)

    def render_html(self):
        return self._html_layout.render(md_render=_mail_md_renderer.render,
                                        **(self.data))

    def render_text(self):
        return self._text_layout.render(**(self.data))


class Mail(object):

    def __init__(self, subject, to=None, cc=None, from_=DEFAULT_NOTIFY_SENDER_ADDR,
                 in_reply_to='', message_id=None, context=None, big=None):
        self.subject = subject
        self.to = [to, ] if isinstance(to, basestring) else to
        self.cc = [cc, ] if isinstance(cc, basestring) else cc
        self.from_addr = from_
        self.in_reply_to = in_reply_to
        self._attachments = []
        self._message_id = message_id
        self._context = context
        self.big = big

    @property
    def context(self):
        return self._context

    @context.setter
    def context(self, ctx):
        if not isinstance(ctx, MailDirectContext):
            raise Exception("ValueError: context should be a MailDirectContext instance")
        self._context = ctx

    @property
    def attachments(self):
        return self._attachments

    def attach(self, filename):
        self._attachments.append(filename)

    def _process_addrs(self, addrs):
        if not addrs:
            return []
        rs = []
        for addr in addrs:
            if isinstance(addr, basestring):
                rs.append(addr)
            elif isinstance(addr, list):
                rs += self._process_addrs(addr)
        return rs

    def generate_msg(self):
        msg = MIMEMultipart('related')
        msgalt = MIMEMultipart('alternative')

        msg['From'] = self.from_addr
        msg['Subject'] = Header(self.subject, 'utf8')
        msg['In-Reply-To'] = self.in_reply_to

        to = set(self._process_addrs(self.to))
        cc = set(self._process_addrs(self.cc)) - to

        if not to:
            to = [TRASH_EMAIL_ADDR, ]

        if to:
            msg['To'] = ', '.join(to)
        if cc:
            msg['Cc'] = ', '.join(cc)
        if self._message_id:
            msg['Message-Id'] = self._message_id

        html = self.context.html
        text = self.context.text

        msg.attach(msgalt)
        msgalt.attach(MIMEText(text, 'plain', 'utf-8'))
        msgalt.attach(MIMEText(html, 'html', 'utf-8'))

        for filename in self.attachments:
            att = MIMEText(open(filename).read(), 'base64', 'utf8')
            att['Content-Type'] = 'application/octet-stream'
            attname = '/' in filename and filename[filename.rfind('/') + 1:] or filename
            att['Content-Disposition'] = 'attachment; filename="%s"' % attname
            msg.attach(att)

        return msg

    def send(self):
        msg = self.generate_msg()
        if self.big:
            send_big_mail(msg)
        else:
            try:
                send_mail(msg, replyable=True)
            except InvalidEmailAddress:
                logging.error("%s %s %s" % (self.from_addr, self.to, self.cc))
                logging.error(self.context.text)

    @classmethod
    def send_mail(cls, subject, to=None, cc=None,
                  from_=DEFAULT_NOTIFY_SENDER_ADDR, in_reply_to='',
                  message_id=None, context=None):
        mail = Mail(subject, to, cc, from_, in_reply_to, message_id)
        mail.context = context
        mail.send()

    @staticmethod
    def default_sender(name):
        return "%s <%s>" % (name, DEFAULT_NOTIFY_SENDER_ADDR)

    @staticmethod
    def customize_sender(name, tag):
        return "%s <%s>" % (name, CUSTOMIZE_NOTIFY_SENDER_ADDR % tag.replace("/", "-"))

    @staticmethod
    def addrs_by_usernames(usernames, target=None):
        addrs = set()
        for username in usernames:
            user = User(username) if username else None
            if user:
                if (target and user.notify_email(target)) or not target:
                    addrs.add(user.email)
                    addrs = addrs.union(user.settings.notif_other_emails)
        return addrs

    @classmethod
    def addrs_by_emails(cls, emails):
        return Mail.addrs_by_usernames(
            [get_author_by_email(email) for email in emails])


if __name__ == '__main__':
    context = MailContext('_', title='test title', content='text content')
    mail = Mail("test")
    mail.context = context
    mail.send()
