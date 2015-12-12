# -*- coding: utf-8 -*-
from tests.base import TestCase
from vilya.models.pull import PullRequest
from vilya.models.ticket import Ticket, TicketComment
from vilya.models.linecomment import PullLineComment
from tests.utils import mkdtemp, setup_repos
from vilya.models.consts import LINECOMMENT_INDEX_EMPTY


class TicketTest(TestCase):

    def setUp(self):
        TestCase.setUp(self)
        _, self.proj1, _, self.proj1_fork = setup_repos(
            mkdtemp(), 'testproject1')
        _, self.proj2, _, self.proj2_fork = setup_repos(
            mkdtemp(), 'testproject2')

    def test_ticket_gets_by_author(self):
        title = 'test title'
        desc = 'test desc'
        author = 'testuser'
        Ticket.add(self.proj1.id, title, desc, author)
        assert Ticket.gets_by_author(author) != []

    def test_ticket_gets_all_opened(self):
        title = 'test title'
        desc = 'test desc'
        author = 'testuser'
        Ticket.add(self.proj1.id, title, desc, author)
        assert Ticket.gets_all_opened() != []

    def test_ticket_gets_by_proj(self):
        title = 'test title'
        desc = 'test desc'
        author = 'testuser'
        Ticket.add(self.proj1.id, title, desc, author)
        assert Ticket.gets_by_proj(self.proj1.id)

    def test_ticket_gets_by_proj_and_author(self):
        title = 'test title'
        desc = 'test desc'
        author = 'testuser'
        Ticket.add(self.proj1.id, title, desc, author)
        assert Ticket.gets_by_proj_and_author(self.proj1.id, author)
        assert not Ticket.gets_by_proj_and_author(
            self.proj1.id, author='anonuser')

    def test_ticket(self):
        title = 'test title'
        desc = 'test desc'
        author = 'testuser'
        p1_t1 = Ticket.add(self.proj1.id, title, desc, author)
        pullreq1 = PullRequest.open(
            self.proj1_fork, 'master', self.proj1, 'master')
        pullreq1 = pullreq1.insert(p1_t1.ticket_number)
        assert p1_t1.ticket_id == 1
        assert p1_t1.title == title
        assert p1_t1.description == desc
        assert p1_t1.author == author
        p2_t1 = Ticket.add(self.proj2.id, title, desc, author)
        pullreq2 = PullRequest.open(
            self.proj2_fork, 'master', self.proj2, 'master')
        pullreq2 = pullreq2.insert(p2_t1.ticket_number)
        assert p2_t1.ticket_id == 1
        ticket = Ticket.get_by_projectid_and_ticketnumber(
            self.proj1.id, p1_t1.ticket_id)
        assert ticket.id == p1_t1.id
        ticket = Ticket.get_by_projectid_and_ticketnumber(
            self.proj2.id, p2_t1.ticket_id)
        assert ticket.id == p2_t1.id

    def test_ticket_commit(self):
        title = 'test title'
        desc = 'test desc'
        author = 'testuser'
        p1_t1 = Ticket.add(self.proj1.id, title, desc, author)
        pullreq1 = PullRequest.open(
            self.proj1_fork, 'master', self.proj1, 'master')
        pullreq1 = pullreq1.insert(p1_t1.ticket_number)

        # ticket commits
        commits_value = '454418c61cd7ef1a65818121746b45064a5af5d6,454418c61cd7ef1a65818121746b45064a5af574'  # noqa
        p1_t1.add_commits(commits_value, author)
        commits = p1_t1.get_commits()
        assert len(commits) == 1
        assert commits[0].commits == commits_value

    def test_ticket_comment(self):
        title = 'test title'
        desc = 'test desc'
        author = 'testuser'
        p1_t1 = Ticket.add(self.proj1.id, title, desc, author)
        pullreq1 = PullRequest.open(
            self.proj1_fork, 'master', self.proj1, 'master')
        pullreq1 = pullreq1.insert(p1_t1.ticket_number)

        # add ticket comment
        comment = p1_t1.add_comment('comment contet', author)
        assert comment is not None

        # update ticket_comment
        assert comment.content == 'comment contet'
        comment.update('comment content updated')
        comment = TicketComment.get(id=comment.id)
        assert comment.content == 'comment content updated'

        # delete ticket_comment
        assert len(TicketComment.gets_by_ticketid(p1_t1.id)) == 1
        comment.delete()
        assert TicketComment.gets_by_ticketid(p1_t1.id) == []

    # 重构后修改
    def test_ticket_code_review(self):
        title = 'test title'
        desc = 'test desc'
        author = 'testuser'
        p1_t1 = Ticket.add(self.proj1.id, title, desc, author)
        pullreq1 = PullRequest.open(
            self.proj1_fork, 'master', self.proj1, 'master')
        pullreq1 = pullreq1.insert(p1_t1.ticket_number)

        # ticket code review
        path = '/README.md'
        #position = 10
        from_sha = '454418c61cd7ef1a65818121746b45064a5af5d6'
        oid = '454418c61cd7ef1a65818121746b45064a5af5d6'
        codereview = p1_t1.add_codereview(
            from_sha, '', path, path, oid, oid, LINECOMMENT_INDEX_EMPTY,
            LINECOMMENT_INDEX_EMPTY, author, 'comment content')
        assert codereview.ticket_id == p1_t1.id
        assert codereview.path == path
        assert codereview.from_sha == from_sha

        # test update content
        assert codereview.content == 'comment content'
        codereview.update('content updated')
        codereview = PullLineComment.get(codereview.id)
        assert codereview.content == 'content updated'

        codereviews = PullLineComment.gets_by_target_and_ref(
            p1_t1.id, from_sha)
        assert len(codereviews) == 1
        p1_t1.add_codereview(
            from_sha, '', path, path, oid, oid, LINECOMMENT_INDEX_EMPTY,
            LINECOMMENT_INDEX_EMPTY, author, 'another comment content')
        codereviews = PullLineComment.gets_by_target_and_ref(
            p1_t1.id, from_sha)
        assert len(codereviews) == 2

        # test delete comment
        codereview.delete()
        codereviews = PullLineComment.gets_by_target_and_ref(
            p1_t1.id, from_sha)
        assert len(codereviews) == 1

    def test_ticket_close(self):
        # close ticket
        title = 'test title'
        desc = 'test desc'
        author = 'testuser'

        p2_t1 = Ticket.add(self.proj2.id, title, desc, author)
        pullreq2 = PullRequest.open(
            self.proj2_fork, 'master', self.proj2, 'master')
        pullreq2 = pullreq2.insert(p2_t1.ticket_number)

        assert p2_t1.closed is None
        p2_t1.close('testuser')
        assert Ticket.get(p2_t1.id).closed is not None

    def test_ticket_participants(self):
        # test participants
        title = 'test title'
        desc = 'test desc'
        author = 'testuser'

        p1_t2 = Ticket.add(self.proj1.id, title, desc, author)
        pullreq = PullRequest.open(
            self.proj1_fork, 'master', self.proj1, 'master')
        pullreq = pullreq.insert(p1_t2.ticket_number)
        assert len(p1_t2.participants) == 1
        assert p1_t2.participants[0] == author

        user2 = 'testuser2'
        p1_t2.add_comment('comment contet', user2)
        assert len(p1_t2.participants) == 2
        assert p1_t2.participants[0] == author
        assert p1_t2.participants[1] == user2

    def test_ticket_count(self):
        title = 'test title'
        desc = 'test desc'
        author = 'testuser'

        p1_t1 = Ticket.add(self.proj1.id, title, desc, author)
        pullreq1 = PullRequest.open(
            self.proj1_fork, 'master', self.proj1, 'master')
        pullreq1 = pullreq1.insert(p1_t1.ticket_number)

        p1_t2 = Ticket.add(self.proj1.id, title, desc, author)
        pullreq = PullRequest.open(
            self.proj1_fork, 'master', self.proj1, 'master')
        pullreq = pullreq.insert(p1_t2.ticket_number)

        # test ticket count
        assert int(Ticket.get_count_by_proj(self.proj1.id)) == 2

    def test_ticket_update_desc(self):
        title = 'test title'
        desc = 'test desc'
        author = 'testuser'

        p1_t2 = Ticket.add(self.proj1.id, title, desc, author)
        pullreq = PullRequest.open(
            self.proj1_fork, 'master', self.proj1, 'master')
        pullreq = pullreq.insert(p1_t2.ticket_number)

        new_title = 'this is new title'
        new_desc = 'this is new desc!'
        p1_t2.update(new_title, new_desc)
        p1_t2 = Ticket.get(p1_t2.id)
        assert p1_t2.title == new_title
        assert p1_t2.description == new_desc
