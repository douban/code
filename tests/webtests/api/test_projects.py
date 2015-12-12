# coding: utf-8
import ast

from base import APITestCase
from vilya.models.project import CodeDoubanProject
from tests.utils import delete_project

COMMITS = """  # noqa
[
{"files": [{"type": "deleted", "filepath": "old.txt"}, {"type": "deleted", "filepath": "subdir/old.txt"}, {"type": "deleted", "filepath": "subdir/subdir2/old.txt"}], "name": "XTao", "id": "9119237c2d5aa2c4a110296e255c7ec194711066", "date": "2013-08-28T18:14:29+0800", "message": "Remove old.txt", "email": "xutao@douban.com"},
{"files": [{"type": "added", "filepath": "subdir/README.md"}, {"type": "added", "filepath": "subdir/new.txt"}, {"type": "added", "filepath": "subdir/old.txt"}], "name": "XTao", "id": "066e9e87baf6c6839827b3fe48e4ca697c28be3f", "date": "2013-08-28T18:13:56+0800", "message": "Add subdir", "email": "xutao@douban.com"},
{"files": [{"type": "added", "filepath": "subdir/subdir2/README.md"}, {"type": "added", "filepath": "subdir/subdir2/new.txt"}, {"type": "added", "filepath": "subdir/subdir2/old.txt"}], "name": "XTao", "id": "3542065401137fc6769a34601015abc863d2d7a9", "date": "2013-08-28T18:13:37+0800", "message": "Add subdir2", "email": "xutao@douban.com"},
{"files": [{"type": "modified", "filepath": "new.txt"}, {"type": "modified", "filepath": "old.txt"}], "name": "XTao", "id": "4bc90207e76d68d5cda435e67c5f85a0ce710f44", "date": "2013-08-28T18:10:08+0800", "message": "Add content", "email": "xutao@douban.com"},
{"files": [{"type": "added", "filepath": "old.txt"}], "name": "XTao", "id": "d05aa234b9323dbcd3d0067da45f98e73203dc15", "date": "2013-08-28T18:09:25+0800", "message": "Add old.txt", "email": "xutao@douban.com"}
]
"""


class ProjectsTest(APITestCase):

    def test_project(self):
        project_name = "code"
        product_name = "fire"
        summary = "test"
        owner_id = "lisong_intern"
        delete_project(project_name)
        CodeDoubanProject.add(
            project_name, owner_id=owner_id, summary=summary,
            product=product_name)

        ret = self.app.get("/api/%s/" % project_name, status=200).json
        self.assertEqual(ret['name'], project_name)
        self.assertEqual(ret['product'], product_name)
        self.assertEqual(ret['description'], summary)
        self.assertEqual(ret['owner']['name'], owner_id)
        self.assertEqual(ret['committers_count'], 0)
        self.assertEqual(ret['watched_count'], 0)
        self.assertEqual(ret['forked_count'], 0)
        self.assertEqual(ret['open_issues_count'], 0)
        self.assertEqual(ret['open_tickets_count'], 0)

    def test_personal_project(self):
        project_name = "lisong_intern/code"
        summary = "test"
        owner_id = "lisong_intern"
        delete_project(project_name)
        CodeDoubanProject.add(
            project_name, owner_id=owner_id, summary=summary)

        ret = self.app.get("/api/%s/" % project_name, status=200).json
        self.assertEqual(ret['name'], project_name)
        self.assertEqual(ret['owner']['name'], owner_id)
        self.assertEqual(ret['description'], summary)
        self.assertEqual(ret['committers_count'], 0)
        self.assertEqual(ret['watched_count'], 0)
        self.assertEqual(ret['forked_count'], 0)
        self.assertEqual(ret['open_issues_count'], 0)
        self.assertEqual(ret['open_tickets_count'], 0)

    def test_commits(self):
        """
        Test http://code.dapps.douban.com/api/%s/commits
        """
        project = self.get_temp_project()
        ret = self.app.get("/api/%s/commits" % project.name, status=200).json
        commits = ast.literal_eval(COMMITS)
        for a, b in zip(ret, commits):
            self.assertEqual(a['files'], b['files'])
            self.assertEqual(a['message'], b['message'])
            self.assertEqual(a['name'], b['name'])
            self.assertEqual(a['id'], b['id'])
            self.assertEqual(a['date'], b['date'])
            self.assertEqual(a['email'], b['email'])

    def test_fork(self):
        # FIXME: clean fork project
        project = self.get_temp_project()
        api_token = self.create_api_token('test_user')
        ret = self.app.post_json(
            "/api/repos/%s/forks/" % project.name,
            {}, headers=dict(Authorization="Bearer %s" % api_token.token)
        ).json
        self.assertEqual(ret['owner']['name'], 'test_user')
