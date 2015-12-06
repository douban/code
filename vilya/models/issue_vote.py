# -*- coding: utf-8 -*-
from __future__ import absolute_import

from vilya.libs.store import store, mc, cache

MC_KEY_ISSUE_VOTES_COUNT = 'issue_vote_count:v3:%s'


class Upvote(object):
    def __init__(self, id, issue_id, user_id):
        self.id = id
        self.issue_id = issue_id
        self.user_id = user_id

    @classmethod
    def get_upvotes_by_issue_id(cls, issue_id, limit=3):
        votes = []
        rs = store.execute(
            "select id, issue_id, user_id "
            "from issue_upvotes "
            "where issue_id = %s "
            "order_by id desc "
            "limit %d ",
            (issue_id, limit))
        if rs:
            votes = [cls(*r) for r in rs]
        return votes

    @classmethod
    def get_by_issue_id_and_user_id(cls, issue_id, user_id):
        rs = store.execute(
            "select id, issue_id, user_id "
            "from issue_upvotes "
            "where issue_id = %s "
            "and "
            "user_id = %s ",
            (issue_id, user_id))
        if rs and rs[0]:
            return cls(*rs[0])

    @classmethod
    def add(cls, issue_id, user_id):
        upvote = cls.get_by_issue_id_and_user_id(
            issue_id, user_id)
        if upvote:
            return upvote
        else:
            id = store.execute(
                "insert into issue_upvotes "
                "(issue_id, user_id) "
                "values(%s, %s)",
                (issue_id, user_id))
            store.commit()
            mc.delete(MC_KEY_ISSUE_VOTES_COUNT % issue_id)
            return cls(id=id, issue_id=issue_id, user_id=user_id)

    @classmethod
    def delete(cls, issue_id, user_id):
        n = store.execute(
            "delete from issue_upvotes "
            "where issue_id = %s and user_id = %s ",
            (issue_id, user_id))
        if n:
            store.commit()
            mc.delete(MC_KEY_ISSUE_VOTES_COUNT % issue_id)
            return True

    @classmethod
    @cache(MC_KEY_ISSUE_VOTES_COUNT % '{issue_id}')
    def count_by_issue_id(cls, issue_id):
        rs = store.execute(
            "select count(id) from issue_upvotes "
            "where issue_id = %s ",
            (issue_id,))
        res = rs and rs[0]
        return res[0] if res else 0
