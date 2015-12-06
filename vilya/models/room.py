# -*- coding: utf-8 -*-
from vilya.libs.store import store


def _add(name, owner):
    room_id = store.execute("insert into chat_rooms"
                            "(name, author) values(%s, %s)",
                            (name, owner))
    if not room_id:
        store.rollback()
        raise Exception("Unable to insert new room")
    store.commit()
    return room_id


def _get(room_id):
    rs = store.execute("select id, name, author, created_at "
                       "from chat_rooms where id = %s", (room_id,))
    return rs[0] if rs else None


class Room(object):

    def __init__(self, room_id, name, owner, created_at):
        self.id = room_id
        self.name = name
        self.owner = owner
        self.created_at = created_at

    @classmethod
    def get(cls, room_id):
        c = _get(room_id)
        return cls(*c) if c else None

    @classmethod
    def get_all_rooms(cls):
        rs = store.execute(
            "select id, name, author, created_at from chat_rooms order by id")

        return [cls(*r) for r in rs]

    @classmethod
    def add(cls, name, owner):
        new_room_id = _add(name, owner)
        new_room = cls.get(new_room_id)
        return new_room

    @classmethod
    def exists(cls, name):
        rs = store.execute("select id from chat_rooms "
                           "where name=%s", (name,))
        return not len(rs) == 0

    @classmethod
    def delete(cls, name):
        rs = store.execute("delete from chat_rooms "
                           "where name=%s", (name,))
        if rs:
            store.commit()
            return True
        return False
