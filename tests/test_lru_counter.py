# -*- coding: utf-8 -*-

from tests.base import TestCase

from vilya.models.lru_counter import LRUCounter


class TestLRUCounter(TestCase):
    def test_lru_counter(self):
        ids = range(5)
        user = 'lihan'
        counter = LRUCounter(user, ids)
        counter.use(ids[-1])
        ret = counter.sort()
        assert ret == [4, 0, 1, 2, 3]
