# encoding: utf-8
from base import APITestCase
from vilya.models.project import CodeDoubanProject
from tests.utils import delete_project


class UserTest(APITestCase):
    def test_user(self):
        user_name = 'zhangchi'
        ret = self.app.get("/api/users/%s" % user_name, status=200).json
        self.assertEqual(ret['is_intern'], False)
        self.assertTrue('url' in ret)
        self.assertTrue('avatar_url' in ret)
        self.assertTrue(isinstance(ret['badges'], list))

    def test_intern(self):
        user_name = 'lisong_intern'
        ret = self.app.get("/api/users/%s" % user_name, status=200).json
        self.assertEqual(ret['name'], user_name)
        self.assertTrue('url' in ret)
        self.assertTrue('avatar_url' in ret)
        self.assertEqual(ret['is_intern'], True)
        self.assertTrue(isinstance(ret['badges'], list))

    def test_get_current_auth_user(self):
        user_name = 'xingben'
        api_token = self.create_api_token('xingben')
        ret = self.app.get(
            "/api/user/",
            headers=dict(Authorization="Bearer %s" % api_token.token),
            status=200
        ).json
        self.assertEqual(ret['name'], user_name)
        self.assertTrue('url' in ret)
        self.assertTrue('avatar_url' in ret)
        self.assertTrue(isinstance(ret['badges'], list))

    def test_get_my_projects(self):
        project_name = "code"
        product_name = "fire"
        summary = "test"
        owner_id = "xingben"
        for i in range(5):
            delete_project("%s%d" % (project_name, i))
            CodeDoubanProject.add(
                "%s%d" % (project_name, i),
                owner_id=owner_id,
                summary=summary,
                product=product_name
            )
        api_token = self.create_api_token('xingben')
        ret = self.app.get(
            "/api/user/repos",
            headers=dict(Authorization="Bearer %s" % api_token.token),
            status=200
        ).json
        self.assertEquals(len(ret), 5)
        self.assertTrue('name' in ret[0])
        self.assertTrue('description' in ret[0])
