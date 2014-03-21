from framework import *
from unittest import TestCase
from vilya.models.board import Board


class TestBoard(TestCase):

    def setUp(self):
        super(TestBoard, self).setUp()

    def tearDown(self):
        super(TestBoard, self).tearDown()
        store.execute('truncate table boards')
        store.commit()

    def test_create(self):
        name = "board"
        desc = "description"
        role = 1
        position = 1
        number = 2
        board = Board.create(name=name,
                             description=desc,
                             role=role,
                             position=position,
                             number=number,
                             project_id=2,
                             creator_id=3)
        self.assertEqual(board.name, name)
        self.assertEqual(board.description, desc)
        self.assertEqual(board.role, role)
        self.assertEqual(board.position, position)
        self.assertEqual(board.number, number)
        self.assertEqual(board.project_id, 2)
        self.assertEqual(board.creator_id, 3)
        self.assertIsNone(board.archiver_id)
        self.assertIsNotNone(board.created_at)
        self.assertIsNotNone(board.updated_at)
        self.assertIsNone(board.archived_at)
