# -*- coding: utf-8 -*-

from vilya.libs.template import st
from vilya.views.util import http_method, jsonize
from vilya.models.notification import Notification
from vilya.models.actions.base import ActionScope
from vilya.models.mute import Mute
from vilya.models.project_issue import ProjectIssue

from vilya.models.actions import migrate_notif_data

_q_exports = ['mark', 'read_all', 'mute']


def _q_index(request):
    user = request.user
    if user:
        all = request.get_form_var('all')
        scope = request.get_form_var('scope')
        unread = not all or all != '1'
        scope = ActionScope.getScope(scope) or ''  # 不带scope则默认所有

        actions = Notification.get_data(user.name)

        # 迁移数据
        all_actions = [migrate_notif_data(action, user.name)
                       for action in actions]

        if scope:
            actions = [action for action in all_actions
                       if action.get('scope') == scope]
        else:
            actions = all_actions

        if unread:
            actions = [action for action in actions if not action.get('read')]
            count_dict = {s: len([a for a in all_actions
                          if a.get('scope') == s and not a.get('read')])
                          for s in ActionScope.all_scopes}
        else:
            count_dict = {s: len([a for a in all_actions
                          if a.get('scope') == s])
                          for s in ActionScope.all_scopes}
        count_dict['all'] = sum(count_dict.values())

        return st('notifications.html', **locals())
    else:
        return request.redirect("/hub/teams")


def _q_lookup(request, uid):
    return RecursorUI(uid)


class RecursorUI(object):
    ''' mark when redirect '''
    _q_exports = []

    def __init__(self, part):
        self.parts = [part]

    def _q_lookup(self, request, part):
        self.parts.append(part)
        return self

    def _q_index(self, request):
        uid = '/'.join(self.parts)
        if uid:
            user = request.user
            Notification.mark_as_read(user.name, uid)
        url = request.get_form_var('url')
        # TODO fix request.query.url
        return request.redirect(url)


@http_method(methods=["POST"])
@jsonize
def mark(request):
    ''' mark by uids '''
    user = request.user
    if user:
        uids = request.get_form_var('uids', [])
        if isinstance(uids, basestring):
            uids = [uids]
        for uid in uids:
            Notification.mark_as_read(user.name, uid)
        return dict(r=0)
    else:
        return dict(r=1)


def read_all(request):
    ''' mark all '''
    user = request.user
    if user:
        Notification.mark_all_as_read(user.name)
        return request.redirect('/hub/notification')
    else:
        return request.redirect("/hub/teams")


# TODO: support unmute
@http_method(methods=["POST"])
@jsonize
def mute(request):
    ''' mute ticket(pr) or issue, just 'project' scope yet. '''
    user = request.user
    if user:
        entry_type = request.get_form_var('type', '')
        target = request.get_form_var('target', '')
        entry_id = request.get_form_var('id', '')
        if entry_type == 'pull':
            Mute.mute('ticket', target, entry_id, user)
        elif entry_type == 'issue':
            # TODO: models.issue.leave or mute
            issue = ProjectIssue.get_by_proj_name_and_number(target, entry_id)
            if user.name != issue.creator_id:
                issue.delete_participant(user.name)
        return dict(r=0)
    else:
        return dict(r=1)
