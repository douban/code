# -*- coding: utf-8 -*-

from datetime import datetime

from vilya.libs.store import store, IntegrityError


class UserFavItem(object):

    def __init__(self, id, user_id, target_id, kind, time):
        self.id = id
        self.user_id = user_id
        self.target_id = target_id
        self.kind = kind
        self.time = time

    @classmethod
    def add(cls, user_id, target_id, kind, time=None):
        time = datetime.now()
        try:
            store.execute('insert into user_fav '
                          '(user_id, target_id, kind, time) '
                          'values (%s, %s, %s, %s)',
                          (user_id, target_id, kind, time))
            store.commit()
            return True
        except IntegrityError:
            return False

    @classmethod
    def delete_by_user_target_kind(cls, user_id, target_id, kind):
        store.execute(
            'delete from user_fav '
            'where user_id=%s and target_id=%s and kind=%s',
            (user_id, target_id, kind))
        store.commit()

    @classmethod
    def gets_by_user_kind(cls, user_id, kind=None):
        if not user_id:
            return []
        if kind:
            rs = store.execute(
                'select id, user_id, target_id, kind, time from user_fav '
                'where user_id=%s and kind=%s order by id desc',
                (user_id, kind))
        else:
            rs = store.execute(
                'select id, user_id, target_id, kind, time from user_fav '
                'where user_id=%s order by id desc', (user_id,))
        return [cls(*r) for r in rs]

    @classmethod
    def get_target_ids_by_user_kind(cls, user_id, kind):
        favs = cls.gets_by_user_kind(user_id, kind)
        return [str(f.target_id) for f in favs]

    @classmethod
    def is_liked_by_user(cls, user_id, kind, target_id):
        return str(target_id) in cls.get_target_ids_by_user_kind(
            user_id, kind)
