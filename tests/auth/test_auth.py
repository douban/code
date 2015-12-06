# encoding: utf-8
from tests.base import TestCase
from webtest import TestApp
import app as M
from base64 import b64encode


class BasicAuthTest(TestCase):

    def test_login(self):
        app = TestApp(M.app)
        headers = {
            "authorization": "Basic %s" % b64encode("doubugreporter:hobbits")}
        r = app.get('/', headers=headers)
        assert r.status_int == 200
        assert 'doubugreporter' in r

    def test_invalid_login(self):
        app = TestApp(M.app)
        headers = {
            "authorization": "Basic%s" % b64encode("doubugreporter:hobbits")}
        app.get('/', headers=headers, status=401)

    def test_unauthorized_login(self):
        app = TestApp(M.app)
        headers = {
            "authorization": "Basic %s" % b64encode("doubugreporter:hobbitsxx")}
        app.get('/', headers=headers, status=401)
