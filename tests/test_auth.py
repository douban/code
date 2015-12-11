# coding: utf-8

from tests.base import TestCase
from webtest import TestApp
import app as M
from base64 import b64encode


class BasicAuthTest(TestCase):

    def test_login(self):
        app = TestApp(M.app)
        headers = {
            "authorization": "Basic %s" % b64encode("code:code")}
        r = app.get('/', headers=headers)
        assert r.status_int == 302
        assert 'teams' in r

    def test_invalid_login(self):
        app = TestApp(M.app)
        headers = {
            "authorization": "Basic%s" % b64encode("code:code")}
        app.get('/', headers=headers, status=401)

    def test_unauthorized_login(self):
        app = TestApp(M.app)
        headers = {
            "authorization": "Basic %s" % b64encode("doubugreporter:hobbitsxx")}
        app.get('/', headers=headers, status=401)
