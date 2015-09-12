# encoding: utf-8
from tests.base import TestCase
from webtest import TestApp

import app as M


class ValidUserIdTest(TestCase):
    def test_valid_user_id(self):
        app = TestApp(M.app)
        user_id1 = "zhangchi"
        user_id2 = "xingben"
        user_id3 = "huanghuang"
        user_id4 = "zhangchen_intern"
        resp1 = app.get("/people/%s/" % user_id1)
        resp2 = app.get("/people/%s/" % user_id2)
        resp3 = app.get("/people/%s/" % user_id3)
        resp4 = app.get("/people/%s/" % user_id4)

        assert resp1.status_int == 200
        assert 'zhangchi' in resp1.body
        assert resp2.status_int == 200
        assert 'xingben' in resp2.body
        assert resp3.status_int == 200
        assert 'huanghuang' in resp3.body
        assert resp4.status_int == 200
        assert 'zhangchen_intern' in resp4.body

    def test_invalid_user_id(self):
        app = TestApp(M.app)
        user_id1 = "thisisaverylonnnnnnnnnnnnnnnnnngusername"
        user_id2 = "a very bad user id"
        user_id3 = "小松"
        resp1 = app.get("/people/%s/" % user_id1, status=404)
        resp2 = app.get("/people/%s/" % user_id2, status=404)
        resp3 = app.get("/people/%s/" % user_id3, status=404)
