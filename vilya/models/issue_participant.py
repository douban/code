# -*- coding: utf-8 -*-
from __future__ import absolute_import
from datetime import datetime

from vilya.libs.store import store


class IssueParticipant(object):

    def __init__(self, id, issue_id, user_id, created_at):
        self.id = id
        self.issue_id = issue_id
        self.user_id = user_id
        self.created_at = created_at

    @property
    def name(self):
        return self.user_id

    @classmethod
    def add(cls, issue_id, user_id):
        time = datetime.now()
        participant_id = store.execute(
            "insert into issue_participants "
            "(issue_id, user_id, created_at) values (%s, %s, NULL)",
            (issue_id, user_id))
        store.commit()
        return cls(participant_id, issue_id, user_id, time)

    # TODO: 合并 getters?
    @classmethod
    def gets_by_issue_id(cls, id):
        rs = store.execute("select id, issue_id, "
                           "user_id, created_at "
                           "from issue_participants "
                           "where issue_id=%s ",
                           (id,))
        return [cls(*r) for r in rs]

    @classmethod
    def gets_by_user_id(cls, user_id):
        rs = store.execute("select id, issue_id, "
                           "user_id, created_at "
                           "from issue_participants "
                           "where user_id=%s ",
                           (user_id,))
        return [cls(*r) for r in rs]

    @classmethod
    def get_by_issue_id_and_user_id(cls, id, user_id):
        rs = store.execute("select id, issue_id, "
                           "user_id, created_at "
                           "from issue_participants "
                           "where issue_id=%s and user_id=%s",
                           (id, user_id))
        if rs and rs[0]:
            return cls(*rs[0])

    def delete(self):
        n = store.execute("delete from issue_participants "
                          "where id=%s", (self.id,))
        if n:
            store.commit()
            return True
