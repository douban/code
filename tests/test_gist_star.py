from tests.base import TestCase
from vilya.models.gist_star import GistStar

from nose.tools import eq_


class TestGistStar(TestCase):

    def test_gist_star(self):
        gist = self._add_gist()
        user_id = 'testuser'
        gs = GistStar.gets_by_user(user_id)
        gs[0].delete()
        ret = GistStar.add(gist.id, user_id)
        eq_(ret, True)

        ret = GistStar.gets_by_gist(gist.id)
        eq_(len(ret), 1)

        ret = GistStar.gets_by_user(user_id)
        eq_(len(ret), 1)

        ret = GistStar.get_by_gist_and_user(gist.id, user_id)
        assert isinstance(ret, GistStar)

        ret = GistStar.count_by_gist(gist.id)
        eq_(ret, 1)

        ret = GistStar.count_by_user(user_id)
        eq_(ret, 1)

    def test_delete_gist_star(self):
        gist = self._add_gist()
        user_id = 'testuser'
        GistStar.add(gist.id, user_id)
        gist_star = GistStar.get_by_gist_and_user(gist.id, user_id)
        gist_star.delete()

        gist_star = GistStar.get_by_gist_and_user(gist.id, user_id)
        eq_(gist_star, None)
