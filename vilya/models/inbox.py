# -*- coding: utf-8 -*-

from datetime import datetime
from itertools import groupby

from vilya.libs.store import mc
from vilya.libs.irc import send_message

from vilya.config import DOMAIN, DEVELOP_MODE


class Courier(object):

    def __init__(self, reception_list):
        self.inboxes = [Inbox.get(r) for r in set(reception_list)]

    @classmethod
    def to(cls, reception_list):
        return cls(reception_list)

    def add_pull_request_data(self, data):
        for inbox in self.inboxes:
            inbox.add_pull_request(data)

    def add_pull_request_action_data(self, data):
        for inbox in self.inboxes:
            inbox.add_pull_request_action(data)
        send_message(
            data.get('commiter') if data.get(
                'status') != "unmerge" else data.get('owner'),
            "Pull request ( %s ) %s on %s by %s" % (
                DOMAIN + data.get('url'),
                "merged" if data.get('status') != "unmerge" else "posted",
                data.get('to_proj'),
                data.get('owner') if data.get(
                    'status') != "unmerge" else data.get('commiter')
            ))

    def add_code_review_data(self, data):
        for inbox in self.inboxes:
            inbox.add_code_review_action(data)

    def prepare_pull_request_data(self, pullreq, ticket_id, ticket,
                                  status="unmerge", new_version=False):
        if new_version:
            ticket_fields = dict(
                reporter=ticket.author, description=ticket.description,
                owner=pullreq.merge_by or pullreq.to_proj.owner_id,
                summary=ticket.title)
        else:
            ticket_fields = ticket.values
        uid = 'pullrequest-%s-%s-%s' % (pullreq.to_proj, ticket_id, status)

        if new_version:
            pullreq_url = "/%s/pull/%s/" % (
                pullreq.to_proj, ticket.ticket_id)
        else:
            pullreq_url = "/%s/pull/%s" % (pullreq.to_proj, ticket.id)
        to_proj_str = "%s:%s" % (pullreq.to_proj, pullreq.to_branch)
        from_proj_str = "%s:%s" % (pullreq.from_proj, pullreq.from_branch)
        commiter = ticket_fields['reporter']

        data = dict(
            date=datetime.now(),
            url=pullreq_url,
            description=ticket_fields['description'],
            from_proj=from_proj_str,
            to_proj=to_proj_str,
            commiter=commiter,
            owner=ticket_fields['owner'],
            title=ticket_fields['summary'],
            status=status,
            uid=uid,
        )
        return data

    def add_pull_request(self, pullreq, ticket_id, ticket, status="unmerge",
                         new_version=False):
        data = self.prepare_pull_request_data(
            pullreq, ticket_id, ticket, status, new_version)
        self.add_pull_request_data(data)

    def add_pull_request_action(self, pullreq, ticket_id, ticket,
                                status="unmerge", new_version=False):
        data = self.prepare_pull_request_data(
            pullreq, ticket_id, ticket, status, new_version)
        self.add_pull_request_action_data(data)

    def add_code_review(self, ticket, author, text, commit_id):
        ticket_fields = ticket.values
        from vilya.models.pull import PullRequest
        pullreq = PullRequest.get_by_ticket(ticket)
        uid = 'codereview-%s-%s-%s' % (pullreq.to_proj, ticket.id, commit_id)

        data = dict(
            date=datetime.now(),
            url="/%s/pull/%s" % (pullreq.to_proj, ticket.id),
            ticket=ticket.id,
            proj="%s:%s" % (pullreq.to_proj, pullreq.to_branch),
            receiver=ticket_fields['reporter'],
            author=author,
            text=text,
            uid=uid,
        )

        self.add_code_review_data(data)

    def add_new_code_review(self, author, text, pullreq, ticket, comment_id,
                            anchor_id=None):
        ticket_id = ticket.ticket_id
        uid = 'newcodereview-%s-%s-%s' % (
            pullreq.to_proj, ticket_id, comment_id)

        data = dict(
            date=datetime.now(),
            url="/%s/pull/%s/#%s" % (pullreq.to_proj, ticket_id, anchor_id),
            ticket=ticket_id,
            proj="%s:%s" % (pullreq.to_proj, pullreq.to_branch),
            receiver=ticket.author,
            author=author,
            text=text,
            uid=uid,
        )

        self.add_code_review_data(data)


class Counter(object):

    def __init__(self, mckey):
        self._mc = mc
        self.mckey = mckey
        self.counter_mckey = mckey + '/counter'
        self.update(is_force=False)

    def __repr__(self):
        return str(self._mc.get(self.counter_mckey) or 0)

    def __str__(self):
        return str(self._mc.get(self.counter_mckey) or 0)

    def __gt__(self, num):
        count = self._mc.get(self.counter_mckey) or 0
        return count > num

    def incr(self):
        return self._mc.incr(self.counter_mckey)

    def decr(self):
        return self._mc.decr(self.counter_mckey)

    def set(self, num):
        return self._mc.set(self.counter_mckey, num)

    def update(self, is_force=True):
        if is_force:
            self._mc.set(
                self.counter_mckey, len(self._mc.get(self.mckey) or []))
        else:
            self._mc.add(
                self.counter_mckey, len(self._mc.get(self.mckey) or []))


class NotificationsCounter(Counter):

    def update(self, is_force=True):
        if is_force or DEVELOP_MODE:
            self._mc.set(
                self.counter_mckey,
                len([n for n in (
                    self._mc.get(self.mckey) or []) if n.get('unread')])
            )
        else:
            self._mc.add(
                self.counter_mckey,
                len([n for n in (
                    self._mc.get(self.mckey) or []) if n.get('unread')])
            )


class PullrequestsCounter(Counter):

    def update(self, is_force=True):
        pullreqs = self._mc.get(self.mckey) or []
        unmerge_num = len(get_unmerge_pull_request(pullreqs))
        if is_force or DEVELOP_MODE:
            self._mc.set(self.counter_mckey, unmerge_num)
        else:
            self._mc.add(self.counter_mckey, unmerge_num)


def get_unmerge_pull_request(pull_requests):
    """
    每个pullrequest的uid格式是 pullrequest-[project name]-[ticket id]-merge/unmerge，
    这里可以用uid来做分组，得出所有unique的pull request
    """
    pull_requests.sort(key=lambda pull: pull.get('uid').rsplit('-', 1)[0])
    unmerge_pulls = []
    for k, group in groupby(
            pull_requests,
            key=lambda pull: pull.get('uid').rsplit('-', 1)[0]):
        is_merged = False
        unmerge_group = []
        for pull in group:
            if pull.get('status') == 'merged':
                is_merged = True
                break
            unmerge_group.append(pull)
        if not is_merged:
            unmerge_pulls.append(unmerge_group[0])
    return unmerge_pulls


# deprecated ??
class Inbox(object):

    def __init__(self, user):
        self._mc = mc
        self.user = user
        self.pullrequests_mckey = "code/%s/pull_requests" % user
        self.actions_mckey = "code/%s/actions" % user
        self.statuses_mckey = "code/%s/statuses" % user
        self.notifications_mckey = "code/%s/notifications" % user
        self.update()

    @classmethod
    def get(cls, user):
        return cls(user=user)

    def update(self):
        self.pull_requests = self._mc.get(self.pullrequests_mckey) or []
        self.actions = self._mc.get(self.actions_mckey) or []
        self.statuses = self._mc.get(self.statuses_mckey) or []
        self.notifications = self._mc.get(self.notifications_mckey) or []

    @property
    def n_pull_requests(self):
        return PullrequestsCounter(self.pullrequests_mckey)

    @property
    def n_notifications(self):
        return NotificationsCounter(self.notifications_mckey)

    def get_pull_requests(self):
        return self.pull_requests

    def get_unmerge_pull_requests(self):
        return get_unmerge_pull_request(self.pull_requests)

    def add_pull_request(self, pull_request):
        self.update()
        old_msgs = self.pull_requests
        old_msgs.append(pull_request)
        self._mc.set(self.pullrequests_mckey, old_msgs)
        self.update()
        self.n_pull_requests.update()

    def _add_one_notif(self, type_, notif):
        # guibog 20120813 these setdefault are not very good,
        # they will change received param
        # TODO replace with d = {...} and d.update(notif)
        notif.setdefault('type', type_)
        notif.setdefault('unread', True)
        self.update()
        self.n_notifications.incr()
        old_msgs = self.notifications
        old_msgs.append(notif)
        self._mc.set(self.notifications_mckey, old_msgs)
        self.update()

    def _add_one_action(self, type_, action):
        action.setdefault('type', type_)
        self.update()
        old_msgs = self.actions
        old_msgs.append(action)
        self._mc.set(self.actions_mckey, old_msgs)
        self.update()

    def add_status(self, status):
        status.setdefault('type', 'status')
        self.update()
        old_msgs = self.statuses
        old_msgs.append(status)
        self._mc.set(self.statuses_mckey, old_msgs)
        self.update()

    def add_pull_request_action(self, action):
        self._add_one_action('pull_request', action)

    def add_pull_request_notification(self, notification):
        self._add_one_notif('pull_request', notification)

    def get_actions(self):
        return self.actions

    def get_statuses(self):
        return self.statuses

    def add_code_review_action(self, code_review):
        self._add_one_action('code_review', code_review)

    def get_notifications(self):
        return self.notifications

    def add_code_review_notification(self, code_review):
        self._add_one_notif('code_review', code_review)

    def add_issue_notification(self, issue_change):
        self._add_one_notif('issue_change', issue_change)

    def add_commit_comment_notification(self, comment):
        self._add_one_notif('commit_comment', comment)

    def add_commit_comment_action(self, comment):
        self._add_one_action('commit_comment', comment)

    def mark_notification_as_read(self, uid):
        self.update()
        self.n_notifications.decr()
        notifications = []
        for n in self.notifications:
            if n and n.get('uid') == uid:
                n['unread'] = False
            notifications.append(n)
        self._mc.set(self.notifications_mckey, notifications)
        self.update()

    def mark_all_notification_as_read(self):
        self.update()
        notifications = []
        for n in self.notifications:
            n['unread'] = False
            notifications.append(n)
        self._mc.set(self.notifications_mckey, notifications)
        self.n_notifications.set(0)
        self.update()

    def add_commit_action(self, commit):
        commit.setdefault('type', 'commit')
        self.update()
        old_acts = self.actions
        # remove duplicated commit
        for act in old_acts:
            if commit.get('commit_id') == act.get('commit_id'):
                return
        old_acts.append(commit)
        self._mc.set(self.actions_mckey, old_acts)
        self.update()

    def add_recommend_action(self, recommend):
        self._add_one_action('recommend', recommend)

    def add_recommend_notification(self, notification):
        self._add_one_notif('recommend', notification)
