# -*- coding: utf-8 -*-
from datetime import datetime

from vilya.models.user import User
from vilya.libs.store import store
from vilya.libs.signals import gist_commented_signal


class GistComment(object):

    def __init__(self, id, gist_id, user_id, content, created_at, updated_at):
        self.id = id
        self.gist_id = gist_id
        self.user_id = user_id
        self.content = content.decode('utf-8')
        self.created_at = created_at
        self.updated_at = updated_at

    def __repr__(self):
        return '<GistComment id:%s, gist:%s, user:%s>' % (
            self.id, self.gist_id, self.user_id)

    def __eq__(self, target):
        return self.id == target.id

    @classmethod
    def get(cls, id):
        rs = store.execute(
            "select id, gist_id, user_id, content, created_at, updated_at "
            "from gist_comments where id=%s", (id,))
        return rs and cls(*rs[0]) or None

    @classmethod
    def gets_by_gist_id(cls, gist_id):
        rs = store.execute(
            "select id, gist_id, user_id, content, created_at, updated_at "
            "from gist_comments where gist_id=%s", (gist_id,))
        return [cls(*r) for r in rs]

    @classmethod
    def add(cls, gist_id, user_id, content):
        now = datetime.now()
        id = store.execute(
            "insert into gist_comments "
            "(`gist_id`, `user_id`, `content`, `created_at`) "
            "values (%s, %s, %s, %s)", (gist_id, user_id, content, now))
        store.commit()
        gc = cls.get(id)
        gist_commented_signal.send(gc, gist_id=gist_id, comment=gc)
        return gc

    @property
    def author(self):
        return User(self.user_id)

    @property
    def url(self):
        from vilya.models.gist import Gist
        return '%s/#comment-%s' % (Gist.get(self.gist_id).url, self.id)

    def as_dict(self):
        ret = {
            "id": self.id,
            "content": self.content,
            "user": self.author.as_dict(),
            "created_at": self.created_at.strftime('%Y-%m-%dT%H:%M:%S')
        }
        return ret

    def can_delete(self, username):
        return username == self.author.name

    def update(self, content):
        store.execute("update gist_comments set content=%s where id=%s",
                      (content, self.id))
        store.commit()

    def delete(self):
        store.execute("delete from gist_comments where id=%s", (self.id,))
        store.commit()
