from tests.base import TestCase
from vilya.models.gist import Gist

from nose.tools import eq_


class TestGist(TestCase):

    def test_gist_star_n_star_unstar_is_starred(self):
        gist = self._add_gist()
        user_id = 'testuser'

        ret = gist.star(user_id)
        eq_(ret, True)

        ret = gist.n_star
        eq_(ret, 1)

        ret = gist.is_starred(user_id)
        eq_(ret, True)

        ret = gist.unstar(user_id)
        eq_(ret, True)

        ret = gist.is_starred(user_id)
        eq_(ret, False)

    def test_gist_fork_n_fork_forks(self):
        gist = self._add_gist()
        user_id = 'testuser'

        ret = gist.fork(user_id)
        assert isinstance(ret, Gist)

        ret = gist.n_fork
        eq_(ret, 1)

        ret = gist.forks
        assert all([isinstance(r, Gist) for r in ret])

    def test_gist_n_revision_n_comments(self):
        gist = self._add_gist()

        ret = gist.n_revision
        eq_(ret, 0)

        ret = gist.n_comments
        eq_(ret, 0)

    def test_gist_files_n_files(self):
        gist = self._add_gist()

        ret = gist.files
        eq_(ret, [])

        ret = gist.n_files
        eq_(ret, 0)

    def test_gist_update(self):
        gist = self._add_gist()
        file_name = 'a.md'
        file_content = '##h1\nhello'

        gist.update('xx', gist_names=[file_name], gist_contents=[file_content])

        ret = gist.files
        eq_(ret, [file_name])

        ret = gist.n_files
        eq_(ret, 1)

    def test_gist_gets_classmethod(self):
        gist = self._add_gist()
        user_id = 'testuser'

        ret = Gist.gets_by_owner(user_id)
        assert all([isinstance(r, Gist) for r in ret])

        gist.fork(user_id)
        ret = Gist.forks_by_user(user_id)
        assert all([isinstance(r, Gist) for r in ret])

        ret = Gist.publics_by_user(user_id)
        assert all([isinstance(r, Gist) for r in ret])

        ret = Gist.secrets_by_user(user_id)
        assert all([isinstance(r, Gist) for r in ret])

    def test_gist_count_classmethod(self):
        gist = self._add_gist()
        user_id = 'testuser'

        ret = Gist.count_user_all(user_id)
        eq_(ret, 1)

        gist.fork(user_id)
        ret = Gist.count_user_fork(user_id)
        eq_(ret, 1)

        gist.star(user_id)
        ret = Gist.count_user_star(user_id)
        eq_(ret, 1)

        ret = Gist.count_public_by_user(user_id)
        eq_(ret, 2)

        ret = Gist.count_secret_by_user(user_id)
        eq_(ret, 0)

    def test_gist_delete(self):
        gist = self._add_gist()
        gist_id = gist.id
        gist.delete()

        ret = Gist.get(gist_id)
        eq_(ret, None)
