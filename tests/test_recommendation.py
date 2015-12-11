# -*- coding: utf-8 -*-

from tests.base import TestCase

from vilya.models.recommendation import Recommendation


class RecommendationTest(TestCase):

    def setUp(self):
        TestCase.setUp(self)
        self.user1 = 'testuser1'
        self.user2 = 'testuser2'
        self.user3 = 'testuser3'
        self.user4 = 'testuser4'
        self.user5 = 'testuser5'

    def test_recommendation(self):
        self.clean_up()
        # lets praise user1
        content = 'Goooooood!'
        r1 = Recommendation.add(self.user2, self.user1, content)
        assert r1.from_user == self.user2
        assert r1.to_user == self.user1
        assert r1.content == content

        r2 = Recommendation.add(self.user3, self.user1, content)
        assert r2.from_user == self.user3
        assert r2.to_user == self.user1
        assert r2.content == content

        r3 = Recommendation.add(self.user4, self.user1, content)
        assert r3.from_user == self.user4
        assert r3.to_user == self.user1
        assert r3.content == content

        r4 = Recommendation.add(self.user1, self.user1, content)
        assert r4 is None

        rs = Recommendation.gets_by_user(self.user1)
        assert len(rs) == len([self.user2, self.user3, self.user4])
        # check default sort
        assert rs[0].id == r3.id

    def test_recommendation_vote(self):
        self.clean_up()
        content = 'Goooooood!'
        r1 = Recommendation.add(self.user2, self.user1, content)
        assert r1.from_user == self.user2
        assert r1.to_user == self.user1
        assert r1.content == content

        r1.add_vote(self.user3)
        r1.add_vote(self.user4)

        assert Recommendation.get(
            r1.id).n_vote == len([self.user3, self.user4])

        # duplicate vote
        r1.add_vote(self.user3)
        r1 = Recommendation.get(r1.id)
        assert Recommendation.get(
            r1.id).n_vote == len([self.user3, self.user4])

        assert r1.is_voted(self.user5) is False

        # last vote
        r1.add_vote(self.user5)
        assert Recommendation.get(
            r1.id).n_vote == len([self.user3, self.user4, self.user5])

        # check sord, more vote more ahead
        r2 = Recommendation.add(self.user3, self.user1, content)
        rs = Recommendation.gets_by_user(self.user1)
        assert len(rs) == len([self.user2, self.user3])
        # check default sort
        assert rs[0].id == r1.id

        assert r1.is_voted(self.user3)
        assert r1.is_voted(self.user4)
        assert r1.is_voted(self.user5)
        assert r1.is_voted(self.user1) is False

        assert r2.is_voted(self.user2) is False
        assert r2.is_voted(self.user3) is False
        assert r2.is_voted(self.user5) is False

    def clean_up(self):
        rcs = Recommendation.gets()
        for rc in rcs:
            rc.delete()
