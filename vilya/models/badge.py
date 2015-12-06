# -*- coding: utf-8 -*-
from datetime import datetime

from vilya.libs.store import store, mc

KIND_USER = 1001
MC_NEW_BADGE = 'newbadge:%s:%s'


class BadgeItem(object):

    def __init__(self, badge_id, item_id, reason=None, date=None):
        self.badge_id = badge_id
        self.item_id = item_id
        self.reason = reason
        self.date = date

    def __str__(self):
        return ','.join([self.badge_id, self.item_id, self.reason, self.date])

    @property
    def badge(self):
        return Badge.get(self.badge_id)

    def as_dic(self):
        badge = self.badge
        if badge:
            return {"reason": self.reason,
                    "date": self.date,
                    "badge": badge.as_dic()}


class Badge(object):

    def __init__(self, id, name, summary):
        self.id = id
        self.name = name
        self.summary = summary

    def __repr__(self):
        return '<Badge(%s)>' % self.id

    @classmethod
    def add(cls, name, summary):
        b = cls.get_by_name(name)
        if b:
            return b
        params = (name, summary)
        id = store.execute(
            "insert into badge(name, summary) values(%s, %s)", params)
        store.commit()
        return cls(id, name, summary)

    def award(self, item_id, reason=None, kind=KIND_USER):
        params = (item_id, self.id, reason, kind, datetime.now())
        store.execute(
            "insert into badge_item(item_id, badge_id, reason, kind, date) "
            "values(%s, %s, %s, %s, %s)", params)
        store.commit()
        mc_key = MC_NEW_BADGE % (item_id, kind)
        badges = mc.get(mc_key) or []
        badges.append(str(self.id))
        mc.set(mc_key, badges)

    def get_awarded_items(self):
        rs = store.execute(
            "select badge_id, item_id, reason, date from badge_item "
            "where badge_id=%s order by date desc", (self.id,))
        return [BadgeItem(*r) for r in rs]

    def delete(self):
        store.execute("delete from badge where badge_id=%s", (self.id,))
        store.commit()

    @classmethod
    def get(cls, id):
        rs = store.execute(
            "select badge_id, name, summary from badge where badge_id=%s",
            (id,))
        row = rs and rs[0]
        if row:
            return cls(*row)

    @classmethod
    def get_by_name(cls, name):
        rs = store.execute(
            "select badge_id, name, summary from badge where name=%s", (name,))
        row = rs and rs[0]
        if row:
            return cls(*row)

    @classmethod
    def all(cls):
        rs = store.execute("select badge_id, name, summary from badge")
        return rs

    @classmethod
    def get_badges(cls, item_id, kind=KIND_USER):
        params = (item_id, kind)
        rs = store.execute(
            "select badge_id from badge_item where item_id=%s and kind=%s",
            params)
        return [cls.get(badge_id) for badge_id, in rs]

    @classmethod
    def get_badge_items(cls, item_id=None, kind=KIND_USER):
        if item_id or kind != KIND_USER:
            params = (item_id, kind)
            rs = store.execute(
                "select badge_id, item_id, reason, date from badge_item "
                "where item_id=%s and kind=%s", params)
        else:
            rs = store.execute(
                "select badge_id, item_id, reason, date from badge_item "
                "order by date desc")
        return [BadgeItem(*item) for item in rs]

    @classmethod
    def get_new_badges(cls, item_id, kind=KIND_USER):
        badges = mc.get(MC_NEW_BADGE % (item_id, kind)) or []
        return [cls.get(bid) for bid in badges]

    @classmethod
    def clear_new_badges(cls, item_id, kind=KIND_USER):
        mc.delete(MC_NEW_BADGE % (item_id, kind))

    @classmethod
    def get_all_badges(cls):
        badges = cls.all()
        return [cls(*badge) for badge in badges]

    @property
    def url(self):
        return "/badge/%s/" % self.id

    def get_image_url(self):
        return "/static/img/badges/%s.png" % self.id

    def as_dic(self):
        return {"name": self.name,
                "summary": self.summary,
                "image": self.get_image_url(),
                "url": self.url}
