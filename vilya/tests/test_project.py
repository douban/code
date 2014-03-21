from framework import *
from unittest import TestCase
from vilya.libs.store import store
from vilya.models.project import Project


class TestProject(TestCase):

    def setUp(self):
        super(TestProject, self).setUp()

    def tearDown(self):
        super(TestProject, self).tearDown()
        store.execute('truncate table projects')
        store.commit()

    def test_create(self):
        proj_name = "test_project"
        proj = Project.create(name=proj_name, owner_id=1, creator_id=1)
        self.assertEqual(proj.name, proj_name)
        self.assertEqual(proj.owner_id, 1)
        self.assertEqual(proj.creator_id, 1)
        self.assertIsNotNone(proj.created_at)
        self.assertIsNotNone(proj.updated_at)
        self.assertIsNotNone(proj.repo)
        self.assertIsNone(proj.upstream)
        self.assertEqual(len(proj.boards), 5)
        self.assertEqual(len(proj.card_boards), 3)
        self.assertIsNotNone(proj.archive_board)
        self.assertIsNotNone(proj.issue_board)
        self.assertEqual(proj.remote_name, str(proj.id))
