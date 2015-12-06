# -*- coding: utf-8 -*-

import json

from vilya.libs.rdstore import rds
from vilya.libs.text import get_mentions_from_text
from vilya.models.utils import CJsonEncoder

MAX_NOTIFY_COUNT = 100
RDS_PREFIX = 'notification'


def rds_key_for_receiver(receiver):
    return RDS_PREFIX + ':' + receiver


class Notification(object):
    def __init__(self, uid, receivers, data):
        self.receivers = set(receivers)
        self.data = data
        self.uid = uid

    def send(self):
        data = self.data
        data['uid'] = self.uid
        for receiver in self.receivers:
            key = rds_key_for_receiver(receiver)
            rds.lpush(key, json.dumps(data, cls=CJsonEncoder))
            rds.ltrim(key, 0, MAX_NOTIFY_COUNT)

    @classmethod
    def get_data(cls, receiver):
        key = rds_key_for_receiver(receiver)
        raw_data = rds.lrange(key, 0, MAX_NOTIFY_COUNT)
        data = [json.loads(d) for d in raw_data]
        return data

    # 暴露出来是为了给以前数据做迁移
    @classmethod
    def set_data(cls, receiver, field, value, uid=None):
        key = rds_key_for_receiver(receiver)
        datas = cls.get_data(receiver)
        for i, d in enumerate(datas):
            if (uid and d.get('uid') == uid) or (uid is None):
                d[field] = value
                raw_d = json.dumps(d, cls=CJsonEncoder)
                rds.lset(key, i, raw_d)

    @classmethod
    def mark_as_read(cls, receiver, uid):
        if uid is None:
            return
        cls.set_data(receiver, 'read', True, uid)

    # FIXME: hack
    @classmethod
    def mark_as_read_by_pull(cls, receiver, project_name, pull_number):
        key = rds_key_for_receiver(receiver)
        actions = cls.get_data(receiver)
        for i, d in enumerate(actions):
            # scope
            if d.get('scope') != 'project':
                continue
            # project name
            if d.get('target') != project_name:
                continue
            if 'pull' not in d.get('type'):
                continue
            # pull id
            if d.get('entry_id') != int(pull_number):
                continue
            d['read'] = True
            raw_d = json.dumps(d, cls=CJsonEncoder)
            rds.lset(key, i, raw_d)

    # FIXME: hack
    @classmethod
    def mark_as_read_by_issue(cls, receiver, id):
        return

    @classmethod
    def mark_all_as_read(cls, receiver):
        cls.set_data(receiver, 'read', True)

    @classmethod
    def unread_count(cls, receiver):
        datas = cls.get_data(receiver)
        count = 0
        for data in datas:
            if not data.get('read'):
                count += 1
        return count

    @classmethod
    def delete_by_uid(cls, receiver, uid):
        key = rds_key_for_receiver(receiver)
        datas = cls.get_data(receiver)
        for i, d in enumerate(datas):
            if (uid and d.get('uid') == uid):
                # for python dict order, only use lindex
                rds.lrem(key, rds.lindex(key, i))


def get_pr_notify_receivers(author, content, pullreq, ticket,
                            channel="notify", extra_receivers=[]):
    noti_receivers = ticket.participants
    at_users = get_mentions_from_text(content)
    noti_receivers.extend(
        at_users + [ticket.author, pullreq.to_proj.owner_id] + extra_receivers)
    noti_receivers = list(set(noti_receivers))
    # not to notify author himself
    if author in noti_receivers:
        noti_receivers.remove(author)
    return noti_receivers


def get_pr_notify_toaddr_receivers(author, content, pullreq, ticket):
    noti_receivers = []
    at_users = get_mentions_from_text(content)
    noti_receivers.extend(at_users + [ticket.author, pullreq.to_proj.owner_id])
    if author in noti_receivers:
        noti_receivers.remove(author)
    return noti_receivers


def get_pr_notify_ccaddr_receivers(author, toaddr, extra_receivers):
    noti_receivers = []
    noti_receivers.extend(extra_receivers)
    noti_receivers = list(set(noti_receivers) - set(toaddr))
    if author in noti_receivers:
        noti_receivers.remove(author)
    return noti_receivers


def get_issue_notify_receivers(author, content, target, issue,
                               channel='notify'):
    noti_receivers = []
    at_users = get_mentions_from_text(content)
    participants = [p.user_id for p in issue.participants if p]
    if issue.target_type == "project":
        noti_receivers.extend(
            at_users + [issue.creator_id, target.owner_id] + participants)
    elif issue.target_type == "team":
        noti_receivers.extend(
            at_users + [issue.creator_id] + participants + target.user_ids)
    noti_receivers = list(set(noti_receivers))
    # not to notify author himself
    if author in noti_receivers:
        noti_receivers.remove(author)
    return noti_receivers
