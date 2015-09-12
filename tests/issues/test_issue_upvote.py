# encoding: UTF-8

from tests.base import TestCase

from vilya.models.issue import Issue
from vilya.models.team_issue import TeamIssue
from vilya.models.project_issue import ProjectIssue


class TestIssueUpvote(TestCase):

    def setUp(self):
        TestCase.setUp(self)
        self.testuser1 = 'testuser1'
        self.testuser2 = 'testuser2'
        self.testuser3 = 'testuser3'
        self.test_team_issue = TeamIssue.add('test', 'test description',
                                             self.testuser1, team=1)
        self.test_project_issue = ProjectIssue.add(
            'test',  'test description', self.testuser1, project=1)

    def test_vote_and_unvote_team_issue(self):
        assert self.test_team_issue.vote_count == 0
        count = self.test_team_issue.upvote_by_user(self.testuser2)
        assert count == 1
        assert self.test_team_issue.vote_count == 1
        # 同一用户upvote两次，vote数不会增加
        count = self.test_team_issue.upvote_by_user(self.testuser2)
        assert count == 1
        assert self.test_team_issue.vote_count == 1
        count = self.test_team_issue.upvote_by_user(self.testuser3)
        assert count == 2
        assert self.test_team_issue.vote_count == 2
        count = self.test_team_issue.cancel_upvote_by_user(self.testuser2)
        assert count == 1
        assert self.test_team_issue.vote_count == 1
        # 同一用户取消vote两次，vote数不会减少
        count = self.test_team_issue.cancel_upvote_by_user(self.testuser2)
        assert count == 1
        assert self.test_team_issue.vote_count == 1
        count = self.test_team_issue.cancel_upvote_by_user(self.testuser3)
        assert count == 0
        assert self.test_team_issue.vote_count == 0

    def test_vote_and_unvote_project_issue(self):
        assert self.test_project_issue.vote_count == 0
        count = self.test_project_issue.upvote_by_user(self.testuser2)
        assert count == 1
        assert self.test_project_issue.vote_count == 1
        # 同一用户upvote两次，vote数不会增加
        count = self.test_project_issue.upvote_by_user(self.testuser2)
        assert count == 1
        assert self.test_project_issue.vote_count == 1
        count = self.test_project_issue.upvote_by_user(self.testuser3)
        assert count == 2
        assert self.test_project_issue.vote_count == 2
        count = self.test_project_issue.cancel_upvote_by_user(self.testuser2)
        assert count == 1
        assert self.test_project_issue.vote_count == 1
        # 同一用户取消vote两次，vote数不会减少
        count = self.test_project_issue.cancel_upvote_by_user(self.testuser2)
        assert count == 1
        assert self.test_project_issue.vote_count == 1
        count = self.test_project_issue.cancel_upvote_by_user(self.testuser3)
        assert count == 0
        assert self.test_project_issue.vote_count == 0

    def test_team_issue_has_user_upvoted(self):
        count = self.test_team_issue.upvote_by_user(self.testuser2)
        assert count == 1
        assert self.test_team_issue.has_user_voted(self.testuser2)
        assert not self.test_team_issue.has_user_voted(self.testuser1)
        count = self.test_team_issue.cancel_upvote_by_user(self.testuser2)
        assert count == 0
        assert not self.test_team_issue.has_user_voted(self.testuser2)
        assert not self.test_team_issue.has_user_voted(self.testuser1)

    def test_project_issue_has_user_upvoted(self):
        count = self.test_project_issue.upvote_by_user(self.testuser2)
        assert count == 1
        assert self.test_project_issue.has_user_voted(self.testuser2)
        assert not self.test_project_issue.has_user_voted(self.testuser1)
        count = self.test_project_issue.cancel_upvote_by_user(self.testuser2)
        assert count == 0
        assert not self.test_project_issue.has_user_voted(self.testuser2)
        assert not self.test_project_issue.has_user_voted(self.testuser1)

    def test_creator_of_issue_should_not_vote_or_unvote(self):
        count = self.test_team_issue.upvote_by_user(self.testuser1)
        assert count == 0
        assert self.test_team_issue.vote_count == 0
        count = self.test_team_issue.cancel_upvote_by_user(self.testuser1)
        assert count == 0
        assert self.test_team_issue.vote_count == 0

        count = self.test_project_issue.upvote_by_user(self.testuser1)
        assert count == 0
        assert self.test_project_issue.vote_count == 0
        count = self.test_project_issue.cancel_upvote_by_user(self.testuser1)
        assert count == 0
        assert self.test_project_issue.vote_count == 0

    def test_closed_issue_should_not_vote(self):
        self.test_team_issue.close(self.testuser1)
        self.test_team_issue = Issue.get_cached_issue(
            self.test_team_issue.issue_id)
        count = self.test_team_issue.upvote_by_user(self.testuser2)
        assert count == 0

        self.test_project_issue.close(self.testuser1)
        self.test_project_issue = Issue.get_cached_issue(
            self.test_project_issue.issue_id)
        count = self.test_project_issue.upvote_by_user(self.testuser2)
        assert count == 0
