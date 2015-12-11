# -*- coding: utf-8 -*-

from vilya.libs.store import store
from dispatches import dispatch


class Recommendation(object):

    def __init__(self, id, from_user, to_user, content, n_vote, created):
        self.id = id
        self.from_user = from_user
        self.to_user = to_user
        self.content = content
        self.created = created
        self.n_vote = n_vote

    @classmethod
    def add(cls, from_user, to_user, content):
        if from_user == to_user:
            return
        recommendation_id = store.execute(
            "insert into codedouban_recommendations "
            "(from_user, to_user, content) "
            "values (%s, %s, %s)",
            (from_user, to_user, content))
        if not recommendation_id:
            store.rollback()
            raise Exception("Unable to insert new recommendation")
        store.commit()
        rec = cls.get(recommendation_id)
        dispatch('recommend', data={'recommend': rec})
        return rec

    @classmethod
    def get(cls, id):
        rs = store.execute(
            "select id, from_user, to_user, content, n_vote, created "
            "from codedouban_recommendations "
            "where id=%s", (id,))
        res = rs and rs[0]
        return cls(*res) if res else None

    def delete(self):
        store.execute(
            "delete from codedouban_recommendations where id=%s", (self.id,))

    @classmethod
    def gets_by_user(cls, owner):
        rs = store.execute(
            "select id, from_user, to_user, content, n_vote, created "
            "from codedouban_recommendations "
            "where to_user=%s order by n_vote desc, id desc", (owner,))
        return [cls(*res) for res in rs]

    @classmethod
    def gets(cls, limit=20, start=0):
        rs = store.execute(
            "select id, from_user, to_user, content, n_vote, created "
            "from codedouban_recommendations order by id desc limit %s,%s",
            (start, limit))
        return [cls(*res) for res in rs]

    def add_vote(self, user):
        rs = store.execute(
            "select id from codedouban_recommendation_votes"
            " where recommendation_id=%s and user=%s", (self.id, user))
        r = rs and rs[0]
        if r:
            return
        vote_id = store.execute(
            "insert into codedouban_recommendation_votes "
            "(recommendation_id, user) "
            "values (%s, %s)",
            (self.id, user))
        if not vote_id:
            store.rollback()
            raise Exception("Unable to insert new vote")

        store.execute("update codedouban_recommendations "
                      "set n_vote=n_vote+1 "
                      "where id=%s", (self.id,))
        store.commit()
        return True

    def is_voted(self, user):
        rs = store.execute(
            "select id from codedouban_recommendation_votes"
            " where recommendation_id=%s and user=%s", (self.id, user))
        r = rs and rs[0]
        if r:
            return True
        return False
