# encoding: utf-8
from base import APITestCase


TITLE = "pull_title"
BODY = "pull_body"


class PullTest(APITestCase):

    def test_commits(self):
        """
        Test http://code.dapps.douban.com/api/%s/pulls/%s/commits
        """
        # TODO: implements this function
        pass

    def test_create_pull(self):
        project = self.get_temp_project()
        fork_project = self.get_temp_project(project)
        api_token = self.create_api_token(project.owner_id)
        ret = self.app.post_json(
            "/api/repos/%s/pulls/" % project.name,
            dict(title=TITLE,
                 body=BODY,
                 base_ref="master",
                 head="chinese",
                 head_repo=fork_project.name),
            headers=dict(Authorization="Bearer %s" % api_token.token)
        ).json
        self.assertEqual(ret['base']['ref'], 'master')
        self.assertEqual(ret['base']['repo']['name'], project.name)
        self.assertEqual(ret['head']['ref'], 'chinese')
        self.assertEqual(ret['head']['repo']['name'], fork_project.name)
        self.assertEqual(ret['title'], TITLE)
        self.assertEqual(ret['description'], BODY)
