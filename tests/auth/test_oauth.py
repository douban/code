# encoding: utf-8
from tests.base import TestCase
from webtest import TestApp
import app as M

from vilya.models.api_token import ApiToken


class OAuthTest(TestCase):

    def test_login(self):
        app = TestApp(M.app)
        user_id = 'testuser'
        apikey = self._add_api_key()
        token = ApiToken.add(apikey.client_id, user_id)
        app.get('/',
                headers=dict(Authorization="Bearer %s" % token.token),
                status=200)

    def test_unauthorized_login(self):
        app = TestApp(M.app)
        r = app.get(
            '/', headers=dict(Authorization="Bearer BAD"),
            status=202)
