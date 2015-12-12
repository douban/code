# encoding: utf-8
from tests.base import TestCase
from webtest import TestApp

import app as M


class TeamsWebTest(TestCase):
    def test_hub_teams(self):
        app = TestApp(M.app)
        resp = app.get('/hub/teams')
        assert resp.status_int == 200
