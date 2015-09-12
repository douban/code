# -*- coding: utf-8 -*-

from tests.base import TestCase

from vilya.models.user import User


class TestUser(TestCase):
    def test_simple_user(self):
        u = User('testu')
        assert u.name == 'testu'
        assert 'douvatar' in u.avatar_url
        assert u.get_badges() == []
        assert u.email == 'testu@douban.com'
        assert u.username == 'testu'
        assert u.url == '/people/testu/'

    def test_user_with_email_from_inside_douba(self):
        u = User('testu', 'testu_email@douban.com')
        assert u.name == 'testu'
        assert 'douvatar' in u.avatar_url
        assert u.get_badges() == []
        assert u.email == 'testu_email@douban.com'
        assert u.username == 'testu'
        assert u.url == '/people/testu/'

    def test_user_with_email_from_outside_douba(self):
        u = User('testu', 'testu_email@test.com')
        assert u.name == 'testu'
        assert 'douvatar' in u.avatar_url
        assert u.get_badges() == []
        assert u.email == 'testu_email@test.com'
        assert u.username == 'testu'
        assert u.url == '/people/testu/'

    def test_get_current_user(self):
        assert not User.get_current_user()

    def test_user_equal(self):
        assert User('tu', 'testu@test.com') == User('tu', 'testu@test.com')
        assert User('tu1', 'testu@test.com') != User('tu2', 'testu@test.com')

    def test_follow(self):
        User('testuser2').follow('testuser1')
        User('testuser3').follow('testuser1')
        assert len(User('testuser1').get_followers()) == 2
        User('testuser3').follow('testuser1')
        assert len(User('testuser1').get_followers()) == 2
        User('testuser3').unfollow('testuser1')
        assert len(User('testuser1').get_followers()) == 1
        User('testuser2').unfollow('testuser1')
        assert len(User('testuser1').get_followers()) == 0

    def test_user_settings(self):
        u = User('testu')
        assert u.settings.show_tips is None
        u.settings.show_tips = True
        assert u.settings.show_tips is True
