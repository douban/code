from tests.base import TestCase
from vilya.models.gist_comment import GistComment

from nose.tools import eq_


class TestGistComment(TestCase):

    def test_gist_comment(self):
        gist = self._add_gist()
        user_id = 'testuser'
        content = 'xxoo'
        new_content = 'ooxx'

        gc = GistComment.add(gist.id, user_id, content)
        assert isinstance(gc, GistComment)

        gcs = GistComment.gets_by_gist_id(gist.id)
        eq_(len(gcs), 1)

        assert gc.can_delete(user_id)

        gc.update(new_content)
        gc = GistComment.get(gc.id)

        eq_(gc.content, new_content)

        gc.delete()
        ret = GistComment.get(gc.id)
        eq_(ret, None)
