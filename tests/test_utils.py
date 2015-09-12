# -*- coding: utf-8 -*-

from tests.base import TestCase

from vilya.models.utils import check_douban_email


class TestUtils(TestCase):
    def test_check_douban_email(self):
        emails = ('testuser@douban.com',
                  'lh_intern@douban.com',
                  'lihan@intern.douban.com',)
        for e in emails:
            assert check_douban_email(e)

        emails = ('testuser@gmail.com',
                  '',
                  None,
                  'whatsyouremailaddrs')
        for e in emails:
            assert not check_douban_email(e)
