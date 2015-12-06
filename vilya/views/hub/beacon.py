# -*- coding: utf-8 -*-

from quixote.errors import TraversalError

from vilya.models.user import User
from vilya.models.notification import Notification

_q_exports = []

# cat hook.gif | base64
EMAIL_HOOK_GIF = "R0lGODlhAQABAID/AP///wAAACwAAAAAAQABAAACAkQBADs="


def _q_index(request):
    return request.redirect('/hub/notification')


def _q_lookup(request, part):
    return BeaconUI(part)


class BeaconUI(object):
    _q_exports = []

    def __init__(self, part):
        self.parts = [part]

    def _q_lookup(self, request, part):
        self.parts.append(part)
        return self

    def _q_index(self, request):
        url = '/'.join(self.parts)
        parts = url.split('.')
        if len(parts) == 2 and parts[1] == 'gif':
            uid, ext = parts
            username = request.get_form_var('user')
            user = User(username) if username else request.user
        else:
            raise TraversalError
        if user and uid:
            tokens = uid.split('-')
            if tokens[0] == 'pullrequest':
                project_name = '-'.join(tokens[1:-2])
                pull_number = tokens[-2]
                Notification.mark_as_read_by_pull(
                    user.name, project_name, pull_number)
            else:
                Notification.mark_as_read(user.name, uid)
        request.response.set_content_type('image/gif')
        return EMAIL_HOOK_GIF.decode('base64')
