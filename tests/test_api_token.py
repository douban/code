from datetime import datetime

from tests.base import TestCase
from vilya.models.api_token import ApiToken

from nose.tools import eq_


class TestApiToken(TestCase):

    def _add_api_token(self):
        apikey = self._add_api_key()
        user_id = 'testuser'
        return ApiToken.add(apikey.client_id, user_id, datetime.now())

    def test_create_api_token(self):
        token = self._add_api_token()
        assert token is not None

    def test_get_api_token(self):
        token = self._add_api_token()
        target_token = ApiToken.get(token.id)
        eq_(token, target_token)

    def test_get_token_by_token(self):
        token = self._add_api_token()
        target_token = ApiToken.get_by_token(token.token)
        eq_(token, target_token)

    def test_get_token_by_refresh_token(self):
        token = self._add_api_token()
        target_token = ApiToken.get_by_refresh_token(token.refresh_token)
        eq_(token, target_token)

    def test_token_dict(self):
        token = self._add_api_token()
        assert isinstance(token.token_dict(), dict)

    def test_token_revoke(self):
        token = self._add_api_token()
        token.revoke()
        eq_(token.expire_time, token.refresh_expire_time)

    def test_token_refresh(self):
        token = self._add_api_token()
        new_token = token.refresh()
        assert isinstance(new_token, ApiToken)
