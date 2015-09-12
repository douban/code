# -*- coding: utf-8 -*-

from tests.base import TestCase

from vilya.models.user import CodeDoubanUserGithub


class TestGithub(TestCase):

    def test_simple_github(self):
        github = CodeDoubanUserGithub(-1, 'testu', 'testug')
        assert github.user_name == 'testug'
        assert github.user_id == 'testu'

    def test_add_github(self):
        github = CodeDoubanUserGithub.add('testu', 'testug')
        assert github.user_name == 'testug'
        assert github.user_id == 'testu'

    def test_get_by_user_name(self):
        g1 = CodeDoubanUserGithub.add('testu1', 'testug1')
        g2 = CodeDoubanUserGithub.add('testu2', 'testug2')
        g3 = CodeDoubanUserGithub.get_by_user_name('testug2')
        assert g3.user_id == 'testu2'
