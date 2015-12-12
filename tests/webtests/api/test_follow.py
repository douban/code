# encoding: utf-8
from .base import APITestCase
from vilya.models.user import User


class FollowTest(APITestCase):
    def setUp(self):
        super(FollowTest, self).setUp()
        user_name1 = 'zhangchi'
        email = '%s@douban.com' % user_name1
        self.zhangchi = User(user_name1, email)
        user_name2 = 'lijunpeng'
        email = '%s@douban.com' % user_name2
        self.lijunpeng = User(user_name2, email)
        self.api_token_zhangchi = self.create_api_token('zhangchi')
        self.api_token_lijunpeng = self.create_api_token('lijunpeng')

    def test_get_auth_user_following(self):
        self.zhangchi.follow('qingfeng')
        self.zhangchi.follow('lisong_intern')
        self.zhangchi.follow('xingben')

        ret = self.app.get(
            "/api/user/following/",
            status=200
        ).json
        self.assertEquals(ret, [])

        ret = self.app.get(
            "/api/user/following/",
            headers=dict(
                Authorization="Bearer %s" % self.api_token_zhangchi.token),
            status=200
        ).json

        self.assertEquals(len(ret), 3)
        user_name_list = map(lambda x: x['username'], ret)
        self.assertTrue('xingben' in user_name_list)

        User('test1', 'test1@douban.com').follow('zhangchi')
        User('test2', 'test2@douban.com').follow('zhangchi')
        ret = self.app.get(
            "/api/user/followers",
            headers=dict(
                Authorization="Bearer %s" % self.api_token_zhangchi.token),
            status=200
        ).json
        self.assertEquals(len(ret), 2)
        user_name_list = map(lambda x: x['username'], ret)
        self.assertTrue('test1' in user_name_list)

    def test_follow(self):
        self.app.get(
            "/api/user/following/%s/" % (self.lijunpeng.username),
            headers=dict(
                Authorization="Bearer %s" % self.api_token_zhangchi.token),
            status=404
        )

        self.app.put(
            "/api/user/following/%s/" % (self.lijunpeng.username),
            headers=dict(
                Authorization="Bearer %s" % self.api_token_zhangchi.token),
            status=204
        )

        self.app.get(
            "/api/user/following/%s/" % (self.lijunpeng.username),
            headers=dict(
                Authorization="Bearer %s" % self.api_token_zhangchi.token),
            status=204
        )

        self.app.delete(
            "/api/user/following/%s/" % (self.lijunpeng.username),
            headers=dict(
                Authorization="Bearer %s" % self.api_token_zhangchi.token),
            status=204
        )

        self.app.get(
            "/api/user/following/%s/" % (self.lijunpeng.username),
            headers=dict(
                Authorization="Bearer %s" % self.api_token_zhangchi.token),
            status=404
        )
