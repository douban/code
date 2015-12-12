# encoding: utf-8
from base import APITestCase

from vilya.models.project import CodeDoubanProject
from vilya.models.project_issue import ProjectIssue
from vilya.models.issue_comment import IssueComment
from tests.utils import delete_project


class ProjectIssueCommentsTest(APITestCase):
    def setUp(self):
        super(ProjectIssueCommentsTest, self).setUp()
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
        title = "test title"
        description = "test desc"
        creator = "test"
        issue = ProjectIssue.add(
            title,
            description,
            creator,
            project=self.project.id
        )
        self.issue = issue
        self.project = project
        self.comment1 = IssueComment.add(
            self.issue.issue_id, 'content1', 'test1')
        self.comment2 = IssueComment.add(
            self.issue.issue_id, 'content2', 'test2')
        self.api_token = self.create_api_token('test1')
        self.api_token2 = self.create_api_token('test2')

    def test_get_issue_comments(self):
        ret = self.app.get(
            "/api/%s/issues/%s/comments/" % (
                self.project.name, self.issue.number),
            status=200
        ).json
        self.assertTrue(isinstance(ret, list))
        self.assertEquals(len(ret), 2)

    def test_create_issue_comment(self):
        api_token = self.create_api_token('test_user')
        comment_content = "sent from iCode"
        ret = self.app.post_json(
            "/api/%s/issues/%s/comments/" % (
                self.project.name, self.issue.number),
            dict(content=comment_content),
            headers=dict(Authorization="Bearer %s" % api_token.token)
        ).json
        self.assertEquals(ret['content'], comment_content)

    def test_get_a_single_issue_comment(self):
        ret = self.app.get(
            "/api/%s/issues/%s/comments/%s/" % (
                self.project.name,
                self.issue.number,
                self.comment1.number
            )
        ).json
        self.assertEquals(ret['content'], self.comment1.content)

    def test_delete_a_single_issue_comment(self):
        # not login
        ret = self.app.delete(
            "/api/%s/issues/%s/comments/%s/" % (
                self.project.name,
                self.issue.number,
                self.comment1.number
            ),
            status=401
        ).json
        self.assertProblemType(ret['type'], "unauthorized")

        # not the author
        ret = self.app.delete(
            "/api/%s/issues/%s/comments/%s/" % (
                self.project.name,
                self.issue.number,
                self.comment1.number
            ),
            status=403,
            headers=dict(Authorization="Bearer %s" % self.api_token2.token)
        ).json
        self.assertProblemType(ret['type'], "not_the_author")

        # delete right
        ret = self.app.delete(
            "/api/%s/issues/%s/comments/%s/" % (
                self.project.name,
                self.issue.number,
                self.comment1.number
            ),
            status=204,
            headers=dict(Authorization="Bearer %s" % self.api_token.token)
        )

        # alright deleted
        ret = self.app.get(
            "/api/%s/issues/%s/comments/%s/" % (
                self.project.name,
                self.issue.number,
                self.comment1.number,
            ),
            status=404
        )

    def test_update_a_single_issue_comment(self):
        new_comment_content = "sent from iCode"

        # not login, will fail
        ret = self.app.patch_json(
            "/api/%s/issues/%s/comments/%s/" % (
                self.project.name,
                self.issue.number,
                self.comment1.number
            ),
            dict(content=new_comment_content),
            status=401
        ).json
        self.assertProblemType(ret['type'], "unauthorized")

        # not the author
        ret = self.app.patch_json(
            "/api/%s/issues/%s/comments/%s/" % (
                self.project.name,
                self.issue.number,
                self.comment1.number
            ),
            dict(content=new_comment_content),
            status=403,
            headers=dict(Authorization="Bearer %s" % self.api_token2.token)
        ).json
        self.assertProblemType(ret['type'], "not_the_author")

        # send invalid json
        ret = self.app.request(
            "/api/%s/issues/%s/comments/%s/" % (
                self.project.name,
                self.issue.number,
                self.comment1.number
            ),
            method="PATCH",
            body="not a valid json",
            status=400,
            headers=dict(Authorization="Bearer %s" % self.api_token.token)
        ).json
        self.assertProblemType(ret['type'], "not_json")

        # only the author can edit comment
        ret = self.app.patch_json(
            "/api/%s/issues/%s/comments/%s/" % (
                self.project.name,
                self.issue.number,
                self.comment1.number
            ),
            dict(content=new_comment_content),
            status=200,
            headers=dict(Authorization="Bearer %s" % self.api_token.token)
        ).json
        self.assertEquals(ret['content'], new_comment_content)
