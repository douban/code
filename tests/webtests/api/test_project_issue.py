# encoding: utf-8
from base import APITestCase

from vilya.models.project import CodeDoubanProject
from vilya.models.project_issue import ProjectIssue
from vilya.models.issue_comment import IssueComment
from tests.utils import delete_project


class ProjectIssueTest(APITestCase):

    def setUp(self):
        super(ProjectIssueTest, self).setUp()
        project_name = "code"
        product_name = "fire"
        summary = "test"
        owner_id = "lisong_intern"
        delete_project(project_name)
        project = CodeDoubanProject.add(
            project_name,
            owner_id=owner_id,
            summary=summary,
            product=product_name
        )
        self.project = project
        self.username = "lisong_intern"
        self.username2 = "zhangchi"
        self.api_token = self.create_api_token(self.username)
        self.api_token2 = self.create_api_token(self.username2)

    def test_project_issues(self):
        ret = self.app.get(
            "/api/%s/issues/" % self.project.name,
            status=200
        ).json
        self.assertTrue(isinstance(ret, list))

    def test_get_single_issue(self):
        title = "test title"
        description = "test desc"
        creator = "test"
        issue = ProjectIssue.add(
            title,
            description,
            creator,
            project=self.project.id
        )
        IssueComment.add(issue.issue_id, 'content', 'test')
        ret = self.app.get(
            "/api/%s/issues/%s/" % (self.project.name, issue.number),
            status=200
        ).json
        self.assertEquals(ret['title'], title)
        self.assertEquals(ret['description'], description)
        self.assertEquals(ret['creator'], creator)
        self.assertEquals(ret['project'], self.project.name)
        self.assertEquals(ret['comments'], 1)

    def test_create_issue_success(self):
        title = "test title"
        description = "test desc"
        tags = ["tag1", "tag2"]
        ret = self.app.post_json(
            "/api/%s/issues/" % (self.project.name),
            dict(
                title=title,
                description=description,
                tags=tags
            ),
            headers=dict(Authorization="Bearer %s" % self.api_token.token),
            status=201
        ).json

        self.assertEquals(ret['title'], title)
        self.assertEquals(ret['description'], description)
        self.assertEquals(ret['creator'], self.username)
        self.assertEquals(ret['project'], self.project.name)
        self.assertEquals(ret['state'], "open")
        self.assertEquals(ret['tags'], tags)

    def test_create_issue_without_tags_success(self):
        title = "test title"
        description = "test desc"
        ret = self.app.post_json(
            "/api/%s/issues/" % (self.project.name),
            dict(
                title=title,
                description=description
            ),
            headers=dict(Authorization="Bearer %s" % self.api_token.token),
            status=201
        ).json

        self.assertEquals(ret['title'], title)
        self.assertEquals(ret['description'], description)
        self.assertEquals(ret['creator'], self.username)
        self.assertEquals(ret['project'], self.project.name)

    def test_create_issue_without_login_fail(self):
        title = "test title"
        description = "test desc"
        self.app.post_json(
            "/api/%s/issues/" % (self.project.name),
            dict(
                title=title,
                description=description
            ),
            status=401
        ).json

    def test_create_issue_without_title_fail(self):
        description = "test desc"
        self.app.post_json(
            "/api/%s/issues/" % (self.project.name),
            dict(
                description=description
            ),
            headers=dict(Authorization="Bearer %s" % self.api_token.token),
            status=422
        ).json

    def test_create_issue_with_invalid_tags_fail(self):
        title = "test title"
        description = "test desc"
        self.app.post_json(
            "/api/%s/issues/" % (self.project.name),
            dict(
                title=title,
                description=description,
                tags={"tag": "a"}
            ),
            headers=dict(Authorization="Bearer %s" % self.api_token.token),
            status=422
        ).json

    def test_upate_issue_not_author_fail(self):
        issue = ProjectIssue.add(
            'old title',
            'old desc',
            self.username,
            project=self.project.id
        )
        title = "new title"
        description = 'new desc'
        ret = self.app.patch_json(
            "/api/%s/issues/%s/" % (self.project.name, issue.number),
            dict(
                title=title,
                description=description
            ),
            headers=dict(Authorization="Bearer %s" % self.api_token2.token),
            status=403
        ).json
        self.assertProblemType(ret['type'], "not_the_author")

    def test_upate_issue(self):
        title = "test title"
        description = "test desc"
        creator = self.username
        issue = ProjectIssue.add(
            title,
            description,
            creator,
            project=self.project.id
        )
        new_title = "new title"
        new_description = 'new desc'
        ret = self.app.patch_json(
            "/api/%s/issues/%s/" % (self.project.name, issue.number),
            dict(
                title=new_title,
                description=new_description,
                state="closed"
            ),
            headers=dict(Authorization="Bearer %s" % self.api_token.token),
        ).json
        self.assertEquals(ret["title"], new_title)
        self.assertEquals(ret["description"], new_description)
        self.assertEquals(ret["state"], "closed")
