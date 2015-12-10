# encoding: utf-8

from contextlib import contextmanager
from nose.tools import eq_, ok_
from MySQLdb import connect

from vilya.models.badge import Badge
from vilya.models.user import User


@contextmanager
def new_badge(username=None):
    badge = Badge.add(name='测试徽章', summary='测试徽章的描述')
    yield badge
    badge.delete()
    if username:
        Badge.clear_new_badges(username)


class TestBadge(object):
    def tearDown(self):
        conn = connect(use_unicode=True)
        cursor = conn.cursor()
        cursor.execute("delete from badge")
        cursor.execute("delete from badge_item")
        conn.commit()

    def test_new_badge(self):
        with new_badge() as badge:
            ok_(badge.name, '测试徽章')
            ok_(Badge.get_by_name(badge.name))

    def test_badge_award_to_user(self):
        username = 'qingfeng'
        with new_badge(username) as badge:
            badge.award(item_id=username)
            badges = Badge.get_badges(item_id=username)
            eq_(len(badges), 1)
            items = badge.get_awarded_items()
            eq_(len(items), 1)

    def test_get_user_badges(self):
        user = User('qingfeng')
        with new_badge(user.username) as badge:
            badge.award(item_id=user.username)
            eq_(len(user.get_badges()), 2)

    def test_get_user_new_badges(self):
        user = User('qingfeng')
        with new_badge(user.username) as badge:
            badge.award(item_id=user.username)
            eq_(len(user.get_new_badges()), 1)
            user.clear_new_badges()
            eq_(len(user.get_new_badges()), 0)
