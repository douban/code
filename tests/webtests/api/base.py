# -*- coding: utf-8 -*-

import shutil

import app as M


from vilya.models.api_key import ApiKey
from vilya.models.api_token import ApiToken
from vilya.models.gist import Gist
from vilya.models.user import User

from webtest import TestApp
from tests.base import TestCase
from tests.utils import get_temp_project


class APITestCase(TestCase):

    def setUp(self):
        self.init_temp_project()
        super(APITestCase, self).setUp()
        self.app = TestApp(M.app)

    def tearDown(self):
        super(APITestCase, self).tearDown()
        self.clean_temp_project()

    def addUser(self, name='api_test_user'):
        return User(name)

    def _add_api_key(self):
        name = 'test'
        desc = ''
        type = ApiKey.TYPE_WEB
        url = 'http://www.douban.com'
        redirect_uri = 'http://www.douban.com/callback'
        owner_id = 'testuser'
        return ApiKey.add(name, desc, type, url, redirect_uri, owner_id)

    def _add_api_token(self, user_id):
        apikey = self._add_api_key()
        return ApiToken.add(apikey.client_id, user_id)

    def create_api_token(self, user_id="test_user"):
        return self._add_api_token(user_id)

    def assertProblemType(self, type_a, type_b):
        self.assertEquals(type_a, type_b)

    def _add_gist(self, description='', owner_id='testuser', is_public=1,
                  gist_names=[], gist_contents=[], fork_from=None):
        return Gist.add(description, owner_id, is_public,
                        gist_names=gist_names, gist_contents=gist_contents,
                        fork_from=fork_from)

    def init_temp_project(self):
        self._temp_paths = []

    def clean_temp_project(self):
        for path in self._temp_paths:
            shutil.rmtree(path)

    def get_temp_project(self, origin=None):
        project = get_temp_project(origin=origin)
        self._temp_paths.append(project.repo_path)
        return project
