# -*- coding: utf-8 -*-

from __future__ import absolute_import

from vilya.libs.auth.decorators import login_required
from vilya.libs.template import st
from vilya.models.sshkey import SSHKey

_q_exports = []


@login_required
def _q_index(request):
    errors = []
    key_lines = ''
    user = request.user
    sshkeys = user.sshkeys
    if request.method == "POST":
        key_lines = request.get_form_var('ssh')
        newsshkeys = []
        errorkeys = []
        for index, line in enumerate(key_lines.splitlines()):
            valid = SSHKey.validate(user.name, line)
            if not valid:
                errorkeys.append((index, line))
                continue
            duplicated = SSHKey.is_duplicated(user.name, line)
            if duplicated:
                errorkeys.append((index, line))
                continue
            newsshkeys.append(line)

        if not errorkeys:
            for key in newsshkeys:
                SSHKey.add(user.name, key)
            return request.redirect('/settings/ssh')

        error_prefix = 'Please check your SSH Key, Line: '
        for no, key in errorkeys:
            error = error_prefix + '%s ' % no
            errors.append(error)
    return st('/settings/ssh.html', **locals())


@login_required
def _q_lookup(request, sshkey_id):
    if request.get_form_var('_method') == 'delete':
        user = request.user
        sshkey = SSHKey.check_own_by_user(user.name, sshkey_id)
        if sshkey:
            sshkey.delete()
        return request.redirect('/settings/ssh')
