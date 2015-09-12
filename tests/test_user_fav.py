# -*- coding: utf-8 -*-

from tests.base import TestCase

from vilya.models.user_fav import UserFavItem
from vilya.models.consts import K_PULL, K_ISSUE


class TestUser(TestCase):

    def test_add_fav(self):
        user_id = "testuser"
        pull_id = 1
        kind = K_PULL
        UserFavItem.add(user_id, pull_id, kind)
        favs = UserFavItem.gets_by_user_kind(user_id)
        assert len(favs) == 1
        fav = favs[0]
        assert fav.target_id == pull_id

        target_ids = UserFavItem.get_target_ids_by_user_kind(user_id, K_PULL)
        assert len(target_ids) == 1
        assert target_ids[0] == str(pull_id)

        assert UserFavItem.is_liked_by_user(user_id, K_PULL, pull_id), True

    def test_delete_fav(self):
        user_id = "testuser"
        pull_id = 1
        kind = K_PULL
        UserFavItem.add(user_id, pull_id, kind)

        issue_id = 3
        kind = K_ISSUE
        UserFavItem.add(user_id, issue_id, kind)

        favs = UserFavItem.gets_by_user_kind(user_id)
        assert len(favs) == 2

        UserFavItem.delete_by_user_target_kind(user_id, pull_id, K_PULL)
        favs = UserFavItem.gets_by_user_kind(user_id)
        assert len(favs) == 1

        UserFavItem.delete_by_user_target_kind(user_id, issue_id, K_ISSUE)
        favs = UserFavItem.gets_by_user_kind(user_id)
        assert len(favs) == 0
