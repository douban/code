# encoding: utf-8
from base import APITestCase


class ApiIndexTest(APITestCase):

    def test_index(self):
        ret = self.app.get(
            "/api/",
            status=200
            ).json
        self.assertTrue(isinstance(ret, dict))
        self.assertTrue('current_user_url' in ret)
        self.assertTrue('following_url' in ret)
        self.assertTrue('user_url' in ret)
        self.assertTrue('team_url' in ret)
        self.assertTrue('gist_url' in ret)
