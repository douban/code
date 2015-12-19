# -*- coding: utf-8 -*-

from __future__ import absolute_import

from vilya.libs.auth.decorators import login_required
from vilya.libs.template import st
from vilya.models.user import CodeDoubanUserGithub

_q_exports = []


@login_required
def _q_index(request):
    errors = []
    user = request.user
    githubs = user.githubs
    if request.method == "POST":
        user_name = request.get_form_var('github')
        errors = CodeDoubanUserGithub.validate(user.name, user_name)
        if not errors:
            CodeDoubanUserGithub.add(user.name, user_name)
            return request.redirect('/settings/github')
    return st('/settings/github.html', **locals())


@login_required
def _q_lookup(request, github_id):
    if request.get_form_var('_method') == 'delete':
        user = request.user
        github = CodeDoubanUserGithub.check_own_by_user(user.name, github_id)
        if github:
            github.delete()
        return request.redirect('/settings/github')
