# encoding: utf-8
from base import APITestCase


class TimelineTest(APITestCase):
    def test_timeline(self):
        ret = self.app.get("/api/timeline", status=200).json
        self.assertTrue(isinstance(ret, list))