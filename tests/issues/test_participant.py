# encoding: UTF-8

from tests.base import TestCase

from vilya.models.issue_participant import IssueParticipant


class TestIssueParticipant(TestCase):

    def test_add(self):
        p = IssueParticipant.add(1, 'test1')
        assert isinstance(p, IssueParticipant)
        assert p.issue_id == 1
        assert p.user_id == 'test1'

    def test_get(self):
        p = IssueParticipant.add(1, 'test1')
        p = IssueParticipant.add(2, 'test1')
        p = IssueParticipant.add(3, 'test1')
        p = IssueParticipant.add(1, 'test2')

        ps = IssueParticipant.gets_by_issue_id(1)
        assert all([isinstance(_p, IssueParticipant) for _p in ps])
        assert len(ps) == 2

        ps = IssueParticipant.gets_by_user_id('test1')
        assert all([isinstance(_p, IssueParticipant) for _p in ps])
        assert len(ps) == 3

        p = IssueParticipant.get_by_issue_id_and_user_id(1, 'test1')
        assert isinstance(p, IssueParticipant)
        assert p.issue_id == 1
        assert p.user_id == 'test1'

    def test_delete(self):
        p = IssueParticipant.add(1, 'test1')
        p = IssueParticipant.add(2, 'test1')
        p = IssueParticipant.add(3, 'test1')
        p = IssueParticipant.add(1, 'test2')

        p.delete()
        p = IssueParticipant.get_by_issue_id_and_user_id(1, 'test2')
        assert p is None
