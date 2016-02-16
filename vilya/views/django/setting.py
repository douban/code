# -*- coding: utf-8 -*-

import json
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from vilya.libs.template import st


@csrf_exempt
def index(request):
    return HttpResponseRedirect("/settings/emails/")


@csrf_exempt
def emails(request):
    from vilya.models.user import CodeDoubanUserEmails
    errors = []
    user = request.user
    emails = user.emails
    if request.method == "POST":
        email = request.POST.get('email')
        errors = CodeDoubanUserEmails.validate(user.name, email)
        if not errors:
            CodeDoubanUserEmails.add(user.name, email)
            return HttpResponseRedirect('/settings/emails')
    return HttpResponse(st('/settings/emails.html', **locals()))


@csrf_exempt
def emails_delete(request, id):
    from vilya.models.user import CodeDoubanUserEmails
    user = request.user
    email = CodeDoubanUserEmails.check_own_by_user(user.name, id)
    if email:
        email.delete()
    return HttpResponseRedirect('/settings/emails')


@csrf_exempt
def emails_set_notif(request, id):
    from vilya.models.user import CodeDoubanUserEmails
    user = request.user
    email = CodeDoubanUserEmails.check_own_by_user(user.name, id)
    if email:
        addr = email.email
        user.settings.notif_other_emails \
            = user.settings.notif_other_emails + [addr]
    return HttpResponseRedirect('/settings/emails')


@csrf_exempt
def emails_un_notif(request, id):
    from vilya.models.user import CodeDoubanUserEmails
    user = request.user
    email = CodeDoubanUserEmails.check_own_by_user(user.name, id)
    if email:
        addr = email.email
        user.settings.notif_other_emails = [
            e for e in user.settings.notif_other_emails
            if e != addr]
    return HttpResponseRedirect('/settings/emails')


@csrf_exempt
def github(request):
    from vilya.models.user import CodeDoubanUserGithub
    errors = []
    user = request.user
    githubs = user.githubs
    if request.method == "POST":
        user_name = request.POST.get('github')
        errors = CodeDoubanUserGithub.validate(user.name, user_name)
        if not errors:
            CodeDoubanUserGithub.add(user.name, user_name)
            return HttpResponseRedirect('/settings/github')
    return HttpResponse(st('/settings/github.html', **locals()))


@csrf_exempt
def github_delete(request, id):
    from vilya.models.user import CodeDoubanUserGithub
    if request.POST.get('_method') == 'delete':
        user = request.user
        github = CodeDoubanUserGithub.check_own_by_user(user.name, id)
        if github:
            github.delete()
        return HttpResponseRedirect('/settings/github')


def notification(request):
    user = request.user
    return HttpResponse(st('settings/notification.html', **locals()))


@csrf_exempt
def notification_setting(request):
    is_on = request.POST.get('is_on')
    notifications_meta = request.POST.get('notifications_meta')
    user = request.user
    result = "success"
    try:
        user.settings.__setattr__(notifications_meta, is_on)
    except Exception:
        result = "fail"
    return HttpResponse(json.dumps({"result": result}))


@csrf_exempt
def ssh(request):
    from vilya.models.sshkey import SSHKey
    errors = []
    key_lines = ''
    user = request.user
    sshkeys = user.sshkeys
    if request.method == "POST":
        key_lines = request.POST.get('ssh')
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
            return HttpResponseRedirect('/settings/ssh')

        error_prefix = 'Please check your SSH Key, Line: '
        for no, key in errorkeys:
            error = error_prefix + '%s ' % no
            errors.append(error)
    return HttpResponse(st('/settings/ssh.html', **locals()))


@csrf_exempt
def ssh_delete(request, id):
    from vilya.models.sshkey import SSHKey
    user = request.user
    if request.POST.get('_method') == 'delete':
        sshkey = SSHKey.check_own_by_user(user.name, id)
        if sshkey:
            sshkey.delete()
        return HttpResponseRedirect('/settings/ssh')


def codereview(request):
    user = request.user
    return HttpResponse(st('settings/codereview.html', **locals()))


@csrf_exempt
def codereview_setting(request):
    is_enable = request.POST.get('is_enable')
    field = request.POST.get('field')
    user = request.user
    result = "success"
    origin = user.settings.__getattr__(field)
    try:
        user.settings.__setattr__(field, is_enable)
    except Exception:
        result = "fail"
    return HttpResponse(json.dumps({"result": result, "origin": origin}))
