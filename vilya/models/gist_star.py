# -*- coding: utf-8 -*-
from vilya.libs.store import store
from vilya.libs.signals import gist_starred_signal


class GistStar(object):

    def __init__(self, id, gist_id, user_id, created_at):
        self.id = id
        self.gist_id = gist_id
        self.user_id = user_id
        self.created_at = created_at

    def __repr__(self):
        return '<GistStar gist:%s, user:%s>' % (self.gist_id, self.user_id)

    def __eq__(self, target):
        return self.id == target.id

    @classmethod
    def get(cls, id):
        rs = store.execute(
            "select id, gist_id, user_id, created_at from gist_stars "
            "where id=%s", (id,))
        if rs:
            return cls(*rs[0])

    @classmethod
    def add(cls, gist_id, user_id):
        id = store.execute("insert into gist_stars (`gist_id`, `user_id`)"
                           "values (%s, %s)", (gist_id, user_id))
        store.commit()
        gs = cls.get(id)
        gist_starred_signal.send(gs, gist_id=gist_id, author=user_id)
        return True

    @classmethod
    def gets_by_gist(cls, gist_id, start=0, limit=50):
        rs = store.execute("select id, gist_id, user_id, created_at "
                           "from gist_stars where gist_id=%s limit %s, %s",
                           (gist_id, start, limit))
        return [cls(*r) for r in rs]

    @classmethod
    def gets_by_user(cls, user_id, start=0, limit=50):
        rs = store.execute("select id, gist_id, user_id, created_at "
                           "from gist_stars where user_id=%s limit %s, %s",
                           (user_id, start, limit))
        return [cls(*r) for r in rs]

    @classmethod
    def get_by_gist_and_user(cls, gist_id, user_id):
        rs = store.execute("select id, gist_id, user_id, created_at "
                           "from gist_stars where gist_id=%s and user_id=%s",
                           (gist_id, user_id))
        return rs and cls(*rs[0]) or None

    @classmethod
    def count_by_gist(cls, gist_id):
        rs = store.execute(
            "select count(1) from gist_stars where gist_id=%s", (gist_id,))
        return rs[0][0]

    @classmethod
    def count_by_user(cls, user_id):
        rs = store.execute(
            "select count(1) from gist_stars where user_id=%s", (user_id,))
        return rs[0][0]

    def delete(self):
        store.execute("delete from gist_stars where id=%s", (self.id,))
        store.commit()
