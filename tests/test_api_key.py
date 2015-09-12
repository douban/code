from tests.base import TestCase
from vilya.models.api_key import ApiKey

from nose.tools import eq_


class TestApiKey(TestCase):

    def test_create_api_key(self):
        apikey = self._add_api_key()
        assert apikey is not None

    def test_get_api_key(self):
        apikey = self._add_api_key()
        target_apikey = ApiKey.get(apikey.id)
        eq_(apikey, target_apikey)

    def test_get_by_client_id(self):
        apikey = self._add_api_key()
        target_apikey = ApiKey.get_by_client_id(apikey.client_id)
        eq_(apikey, target_apikey)
