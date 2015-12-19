# -*- coding: utf-8 -*-

from __future__ import absolute_import

from vilya.libs.auth.decorators import login_required
from vilya.libs.template import st
from vilya.models.user import CodeDoubanUserEmails

_q_exports = []


@login_required
def _q_index(request):
    errors = []
    user = request.user
    emails = user.emails
    if request.method == "POST":
        email = request.get_form_var('email')
        errors = CodeDoubanUserEmails.validate(user.name, email)
        if not errors:
            CodeDoubanUserEmails.add(user.name, email)
            return request.redirect('/settings/emails')
    return st('/settings/emails.html', **locals())


@login_required
def _q_lookup(request, email_id):
    user = request.user
    return EmailUI(user, email_id)


class EmailUI(object):
    _q_exports = ['delete', 'set_notif', 'un_notif']

    def __init__(self, user, email_id):
        self.user = user
        self.email_id = email_id
        self.user_email = CodeDoubanUserEmails.check_own_by_user(user.name,
                                                                 email_id)

    def delete(self, request):
        if self.user_email:
            self.user_email.delete()
        return request.redirect('/settings/emails')

    def set_notif(self, request):
        if self.user_email:
            addr = self.user_email.email
            self.user.settings.notif_other_emails \
                = self.user.settings.notif_other_emails + [addr]
        return request.redirect('/settings/emails')

    def un_notif(self, request):
        if self.user_email:
            addr = self.user_email.email
            self.user.settings.notif_other_emails = [
                e for e in self.user.settings.notif_other_emails
                if e != addr]
        return request.redirect('/settings/emails')
