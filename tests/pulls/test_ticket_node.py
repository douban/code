# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

from tests.base import TestCase
from vilya.models.consts import (
    TICKET_NODE_TYPE_OPEN,
    TICKET_NODE_TYPE_CLOSE,
    TICKET_NODE_TYPE_MERGE,
    TICKET_NODE_TYPE_COMMIT,
    TICKET_NODE_TYPE_COMMENT,
    TICKET_NODE_TYPE_LINECOMMENT)
from vilya.models.ticket import Ticket, TicketRank, TicketNode
from vilya.libs.store import store


class TicketNodeTest(TestCase):

    def test_add(self):
        type = TICKET_NODE_TYPE_OPEN
        type_id = 1
        author = "user1"
        ticket_id = 1
        created_at = datetime.now()
        node = TicketNode.add(type, type_id, author, ticket_id, created_at)
        assert node.type == type
        assert node.type_id == type_id
        assert node.author == author
        assert node.ticket_id == ticket_id
        assert node.created_at.timetuple() == created_at.timetuple()

    def test_get(self):
        clean_up()
        created_at = datetime.now()
        node1 = TicketNode.add(
            TICKET_NODE_TYPE_CLOSE, 0, 'user1', 1, created_at)
        node2 = TicketNode.add(
            TICKET_NODE_TYPE_MERGE, 0, 'user1', 1, created_at)
        node3 = TicketNode.add(
            TICKET_NODE_TYPE_MERGE, 0, 'user1', 2, created_at)
        nodes = TicketNode.gets_by_ticket_id(1)
        assert len(nodes) == 2

        node1 = TicketNode.add(
            TICKET_NODE_TYPE_LINECOMMENT, 1, 'user1', 2, created_at)
        node2 = TicketNode.add(
            TICKET_NODE_TYPE_COMMENT, 1, 'user1', 2, created_at)
        node = TicketNode.get_by_type_id(TICKET_NODE_TYPE_LINECOMMENT, 1)
        assert node.id == node1.id
        assert node.type == node1.type
        assert node.type_id == node1.type_id
        assert node.ticket_id == node1.ticket_id
        node = TicketNode.get_by_type_id(TICKET_NODE_TYPE_COMMIT, 1)
        assert node is None

    def test_delete(self):
        created_at = datetime.now()
        node1 = TicketNode.add(
            TICKET_NODE_TYPE_CLOSE, 0, 'user1', 1, created_at)
        node2 = TicketNode.add(
            TICKET_NODE_TYPE_MERGE, 0, 'user1', 1, created_at)
        node3 = TicketNode.add(
            TICKET_NODE_TYPE_MERGE, 0, 'user1', 2, created_at)
        node = TicketNode.get(id=node2.id)
        assert node is not None
        node2.delete()
        node = TicketNode.get(id=node2.id)
        assert node is None


class Test_Ticket_Rank(TestCase):
    def test_get_last_created_time(self):
        clean_up()
        node1 = TicketNode.add(
            TICKET_NODE_TYPE_COMMENT, 0, 'user1', 1, datetime.now())
        node2 = TicketNode.add(
            TICKET_NODE_TYPE_COMMENT, 0, 'user1', 1, datetime.now())
        node3 = TicketNode.add(
            TICKET_NODE_TYPE_COMMENT, 0, 'user1', 2, datetime.now())
        node4 = TicketNode.add(
            TICKET_NODE_TYPE_LINECOMMENT, 0, 'user1', 2, datetime.now())
        created_at = datetime.now()
        node5 = TicketNode.add(
            TICKET_NODE_TYPE_LINECOMMENT, 0, 'user1', 1, created_at)
        testtime = TicketRank.get_last_created_time(1)
        assert node5.created_at.timetuple() == testtime.timetuple()
        clean_up()

    def test_get_comment_count(self):
        clean_up()
        created_at = datetime.now()
        node1 = TicketNode.add(
            TICKET_NODE_TYPE_COMMENT, 0, 'user1', 1, created_at)
        node2 = TicketNode.add(
            TICKET_NODE_TYPE_COMMENT, 0, 'user1', 1, created_at)
        node3 = TicketNode.add(
            TICKET_NODE_TYPE_LINECOMMENT, 0, 'user1', 1, created_at)
        node4 = TicketNode.add(
            TICKET_NODE_TYPE_COMMENT, 0, 'user1', 2, created_at)
        node5 = TicketNode.add(
            TICKET_NODE_TYPE_LINECOMMENT, 0, 'user1', 2, created_at)
        test_count = TicketRank.get_comment_count(1)
        assert test_count == 2

    def test_get_line_comment_count(self):
        clean_up()
        created_at = datetime.now()
        node1 = TicketNode.add(
            TICKET_NODE_TYPE_COMMENT, 0, 'user1', 1, created_at)
        node2 = TicketNode.add(
            TICKET_NODE_TYPE_COMMENT, 0, 'user1', 1, created_at)
        node3 = TicketNode.add(
            TICKET_NODE_TYPE_LINECOMMENT, 0, 'user1', 1, created_at)
        node4 = TicketNode.add(
            TICKET_NODE_TYPE_COMMENT, 0, 'user1', 2, created_at)
        node5 = TicketNode.add(
            TICKET_NODE_TYPE_LINECOMMENT, 0, 'user1', 2, created_at)
        test_count = TicketRank.get_line_comment_count(1)
        assert test_count == 1

    def test_get_sum_count(self):
        clean_up()
        created_at = datetime.now()
        node1 = TicketNode.add(
            TICKET_NODE_TYPE_COMMENT, 0, 'user1', 1, created_at)
        node2 = TicketNode.add(
            TICKET_NODE_TYPE_COMMENT, 0, 'user1', 1, created_at)
        node3 = TicketNode.add(
            TICKET_NODE_TYPE_LINECOMMENT, 0, 'user1', 1, created_at)
        node4 = TicketNode.add(
            TICKET_NODE_TYPE_COMMENT, 0, 'user1', 2, created_at)
        node5 = TicketNode.add(
            TICKET_NODE_TYPE_LINECOMMENT, 0, 'user1', 2, created_at)
        test_count = TicketRank.get_sum_count(1)
        assert test_count == 3.3

    def test_count_ticket_rank(self):
        clean_up()
        title = 'test title'
        desc = 'test desc'
        author = 'testuser'
        tick1 = Ticket.add(1, title, desc, author)
        tick2 = Ticket.add(2, title, desc, author)
        created_at = datetime.now()
        aDay = timedelta(days=-1)
        yesterday = created_at + aDay
        node1 = TicketNode.add(
            TICKET_NODE_TYPE_COMMENT, 0, 'user1', tick1.id, created_at)
        node2 = TicketNode.add(
            TICKET_NODE_TYPE_COMMENT, 0, 'user1', tick1.id, created_at)
        node3 = TicketNode.add(
            TICKET_NODE_TYPE_LINECOMMENT, 0, 'user1', tick1.id, created_at)
        node4 = TicketNode.add(
            TICKET_NODE_TYPE_COMMENT, 0, 'user1', tick2.id, yesterday)
        node5 = TicketNode.add(
            TICKET_NODE_TYPE_LINECOMMENT, 0, 'user1', tick2.id, yesterday)

        # 验证 已经关闭的 ticket
        store.execute("update codedouban_ticket set time=%s, closed=%s "
                      "where id=%s", (yesterday, created_at, tick2.id))
        store.commit()
        TicketRank.count_ticket_rank(True)
        rank_score2 = TicketRank.get_rank_by_ticket_id(tick2.id)
        rank_s2 = rank_score2[0][0]
        rank2 = 32.07
        assert rank_s2 == rank2

        # 验证 没有关闭的 ticket
        TicketRank.count_ticket_rank(False)
        rank_score1 = TicketRank.get_rank_by_ticket_id(tick1.id)
        rank_s1 = rank_score1[0][0]
        rank1 = 37.97
        assert rank_s1 == rank1


def clean_up():
    for node in TicketNode.gets():
        node.delete()
