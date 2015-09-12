# -*- coding: utf-8 -*-

from tests.base import TestCase
from tests.utils import get_temp_project
from vilya.models.project_issue import ProjectIssue
from vilya.models.milestone import Milestone
from vilya.models.issue_milestone import IssueMilestone


# User mock
class User(object):

    def __init__(self, name):
        self.name = name


class TestIssueMilestone(TestCase):

    def setUp(self):
        super(TestCase, self).setUp()
        self.project = get_temp_project()
        self.issue = ProjectIssue.add('test',
                                      'test description',
                                      'test',
                                      project=self.project.id)
        user = User('testuser')
        project = self.project
        name = "Test Milestone 1"
        ms = Milestone.create_by_project(project, name, user)
        self.milestone = ms

    def tearDown(self):
        self.milestone.delete()
        self.project.delete()
        super(TestCase, self).tearDown()

    def test_add_issue_milestone(self):
        issue = self.issue
        milestone = self.milestone
        user = User('testuser')
        ims = IssueMilestone.create_by_issue(issue, milestone, user)
        self.assertEqual(ims.milestone_id, milestone.id)
        self.assertEqual(int(ims.issue_id), issue.issue_id)

    def test_get_issue_milestone(self):
        issue = self.issue
        milestone = self.milestone
        user = User('testuser')
        ims1 = IssueMilestone.create_by_issue(issue, milestone, user)
        ims = IssueMilestone.get_by_issue(issue)
        self.assertEqual(ims.id, ims1.id)
        self.assertEqual(ims.issue_id, ims1.issue_id)
        self.assertEqual(ims.milestone_id, ims1.milestone_id)
        self.assertEqual(ims.creator_id, ims1.creator_id)

    def test_get_milestone(self):
        issue = self.issue
        milestone = self.milestone
        user = User('testuser')
        ims = IssueMilestone.create_by_issue(issue, milestone, user)
        ms = ims.milestone
        self.assertEqual(ms.id, milestone.id)
        self.assertEqual(ms.target_id, milestone.target_id)
        self.assertEqual(ms.target_type, milestone.target_type)
        self.assertEqual(ms.target_number, milestone.target_number)
        self.assertEqual(ms.creator_id, milestone.creator_id)
