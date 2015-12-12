# encoding: utf-8
from base import APITestCase
from vilya.libs.store import store
from vilya.models.gist_comment import GistComment


class GistTest(APITestCase):
    def setUp(self):
        store.execute('delete from gist_stars where id<10')
        super(GistTest, self).setUp()
        self.gist1 = self._add_gist(
            description='this is my first gist',
            owner_id='xutao'
        )
        self.gist2 = self._add_gist(
            description='this is my second gist',
            owner_id='xutao'
        )
        self.gist3 = self._add_gist(
            description='this is my second gist',
            owner_id='lisong_intern',
            gist_names=["gistname1.txt", "gistname2.txt"],
            gist_contents=["first", "second"]
        )
        self.api_token = self.create_api_token('xutao')
        self.api_token2 = self.create_api_token('lijunpeng')

    def test_your_gists(self):
        ret = self.app.get(
            "/api/gists/",
            status=200,
            headers=dict(Authorization="Bearer %s" % self.api_token.token)
        ).json
        self.assertEquals(len(ret), 10)

    def test_your_starred_gists(self):
        ret = self.app.put(
            "/api/gists/%s/star" % self.gist1.id,
            status=204,
            headers=dict(Authorization="Bearer %s" % self.api_token.token)
        )
        ret = self.app.get(
            "/api/gists/starred",
            status=200,
            headers=dict(Authorization="Bearer %s" % self.api_token.token)
        ).json
        self.assertEquals(len(ret), 1)

    def test_get_a_not_exist_gist(self):
        ret = self.app.get(
            "/api/gists/%s/" % "444444444",
            status=404,
            headers=dict(Authorization="Bearer %s" % self.api_token.token)
        ).json
        self.assertProblemType(ret['type'], "not_found")
        self.assertTrue("gist" in ret["message"])

    def test_get_single_gist(self):
        ret = self.app.get(
            "/api/gists/%s/" % self.gist1.id,
            status=200,
            headers=dict(Authorization="Bearer %s" % self.api_token.token)
        ).json
        self.assertTrue('description' in ret)
        self.assertTrue('files' in ret)
        self.assertTrue('url' in ret)
        self.assertEquals(ret["public"], True)

    def test_get_single_gist_src(self):
        ret = self.app.get(
            "/api/gists/%s/src" % self.gist3.id,
            status=200,
            headers=dict(Authorization="Bearer %s" % self.api_token.token)
        ).json
        self.assertTrue('path' in ret)
        self.assertTrue('type' in ret)
        self.assertTrue(isinstance(ret['src'], list))

    def test_get_single_gist_source(self):
        ret = self.app.get(
            "/api/gists/%s/source" % self.gist3.id,
            status=200,
            headers=dict(Authorization="Bearer %s" % self.api_token.token)
        ).json
        self.assertTrue(isinstance(ret['source'], list))

    def test_create_a_gist(self):
        description = "my gist"
        filename1 = "file1.txt"
        filename2 = "gist.md"
        content1 = "sent from icode"
        content2 = "##sent from icode"

        ret = self.app.post_json(
            "/api/gists/",
            dict(description="my gist", files={
                filename1: {"content": content1},
                filename2: {"content": content2}
            }),
            status=201,
            headers=dict(Authorization="Bearer %s" % self.api_token.token)
        ).json

        self.assertEquals(ret['description'], description)
        self.assertTrue(filename1 in ret["files"])
        self.assertTrue(filename2 in ret["files"])

    def test_create_a_private_gist(self):
        filename1 = "file1.txt"
        filename2 = "gist.md"
        content1 = "sent from icode"
        content2 = "##sent from icode"

        ret = self.app.post_json(
            "/api/gists/",
            dict(description="my gist", public=False, files={
                filename1: {"content": content1},
                filename2: {"content": content2}
            }),
            status=201,
            headers=dict(Authorization="Bearer %s" % self.api_token.token)
        ).json
        gist_id = ret["id"]
        self.assertEquals(ret['public'], False)

        ret = self.app.get(
            "/api/gists/%s/" % gist_id,
            status=403,
            headers=dict(Authorization="Bearer %s" % self.api_token2.token)
        )

    def test_edit_a_gist(self):
        filename1 = "file1.txt"
        filename2 = "gist.md"
        content1 = "sent from icode"
        content2 = "##sent from icode"

        ret = self.app.post_json(
            "/api/gists/",
            dict(description="my gist", files={
                filename1: {"content": content1},
                filename2: {"content": content2}
            }),
            status=201,
            headers=dict(Authorization="Bearer %s" % self.api_token.token)
        ).json
        gist_id = ret["id"]
        new_description = "new gist"
        new_content1 = "########sent from icode"

        ret = self.app.patch_json(
            "/api/gists/%s/" % gist_id,
            dict(description=new_description, files={
                filename1: {"content": new_content1}
            }),
            status=200,
            headers=dict(Authorization="Bearer %s" % self.api_token.token)
        ).json

        self.assertEquals(ret['description'], new_description)
        # self.assertEquals(new_content1, self.app.get(
        #    ret["files"][filename1]['raw_url']).body)
        # self.assertEquals(content2, self.app.get(
        #     ret["files"][filename2]['raw_url']).body)

    def test_star_a_gist(self):
        self.app.put(
            "/api/gists/%s/star" % self.gist1.id,
            status=204,
            headers=dict(Authorization="Bearer %s" % self.api_token.token)
        )

        self.app.get(
            "/api/gists/%s/star" % self.gist1.id,
            status=204,
            headers=dict(Authorization="Bearer %s" % self.api_token.token)
        )

    def test_unstar_a_gist(self):
        self.app.delete(
            "/api/gists/%s/star" % self.gist1.id,
            status=204,
            headers=dict(Authorization="Bearer %s" % self.api_token.token)
        )

        self.app.get(
            "/api/gists/%s/star" % self.gist1.id,
            status=404,
            headers=dict(Authorization="Bearer %s" % self.api_token.token)
        )

    def test_fork_a_gist(self):
        ret = self.app.post(
            "/api/gists/%s/forks" % self.gist1.id,
            status=201,
            headers=dict(Authorization="Bearer %s" % self.api_token2.token)
        ).json
        self.assertTrue('url' in ret)

    def test_delete_a_gist(self):
        self.app.delete(
            "/api/gists/%s/" % self.gist1.id,
            status=204,
            headers=dict(Authorization="Bearer %s" % self.api_token.token)
        )

        self.app.get(
            "/api/gists/%s/" % self.gist1.id,
            status=404,
            headers=dict(Authorization="Bearer %s" % self.api_token.token)
        )

    def test_get_gist_comments(self):
        GistComment.add(self.gist1.id, 'xutao', "sent from iCode")
        GistComment.add(
            self.gist1.id, 'chengeng', "sent from Code for Android")

        ret = self.app.get(
            "/api/gists/%s/comments/" % self.gist1.id,
            status=200,
            headers=dict(Authorization="Bearer %s" % self.api_token.token)
        ).json
        self.assertEquals(len(ret), 2)
