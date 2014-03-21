from framework import *
from unittest import TestCase
from vilya.models.card import Card


class TestCard(TestCase):

    def test_create(self):
        name = "card"
        desc = "description"
        position = 3
        number = 4
        board_id = 1
        project_id = 2
        creator_id = 1
        card = Card.create(name=name,
                           description=desc,
                           position=position,
                           number=number,
                           board_id=board_id,
                           project_id=project_id,
                           creator_id=creator_id)
        self.assertEqual(card.name, name)
        self.assertEqual(card.description, desc)
        self.assertEqual(card.position, position)
        self.assertEqual(card.number, number)
        self.assertEqual(card.board_id, board_id)
        self.assertEqual(card.project_id, project_id)
        self.assertEqual(card.creator_id, creator_id)
        self.assertIsNotNone(card.created_at)
        self.assertIsNone(card.archived_at)
        self.assertIsNone(card.archived_id)
        self.assertIsNone(card.closer_id)
        self.assertIsNone(card.closed_at)
        self.assertIsNone(card.pull)
