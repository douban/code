# -*- coding: utf-8 -*-

from tests.base import TestCase
from tests.utils import get_temp_project
from vilya.models.milestone import Milestone, PROJECT_MILESTONE_TYPE


# User mock
class User(object):

    def __init__(self, name):
        self.name = name


class TestMilestone(TestCase):

    def setUp(self):
        super(TestCase, self).setUp()
        self.project = get_temp_project()

    def tearDown(self):
        self.project.delete()
        super(TestCase, self).tearDown()

    def test_add_milestone(self):
        user = User('testuser')
        project = self.project
        name = "Test Milestone 1"
        ms = Milestone.create_by_project(project, name, user)
        self.assertEqual(ms.name, name)
        self.assertEqual(int(ms.target_id), project.id)
        self.assertEqual(int(ms.target_type), PROJECT_MILESTONE_TYPE)
        self.assertEqual(ms.creator_id, user.name)

    def test_get_milestone(self):
        user1 = User('testuser1')
        user2 = User('testuser2')
        project = self.project
        name1 = "Test Milestone 1"
        name2 = "Test Milestone 2"
        ms1 = Milestone.create_by_project(project, name1, user1)
        ms2 = Milestone.create_by_project(project, name2, user2)

        ms = Milestone.get_by_project(project, number=ms1.target_number)
        self.assertEqual(ms.name, name1)
        self.assertEqual(int(ms.target_id), project.id)
        self.assertEqual(ms.id, ms1.id)
        self.assertEqual(ms.target_number, ms1.target_number)
        self.assertEqual(ms.creator_id, user1.name)

        ms = Milestone.get_by_project(project, name=name2)
        self.assertEqual(ms.name, name2)
        self.assertEqual(int(ms.target_id), project.id)
        self.assertEqual(ms.id, ms2.id)
        self.assertEqual(ms.target_number, ms2.target_number)
        self.assertEqual(ms.creator_id, user2.name)
