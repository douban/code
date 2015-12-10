# -*- coding: utf-8 -*-

from tests.base import TestCase

from vilya.models import comment

T_PROJ_ID = 123
T_PROJ_ID_2 = 135
T_REF = '2a200e45b0e223d13477e'
T_REF_2 = '2a200e45b0e223d13aaaa'
T_AUTHOR = 'user1'
T_CONTENT = 'test comment content'
T_CONTENT2 = 'test comment content 2'


class TestCommentFuncts(TestCase):
    def test_add_comment(self):
        cid1 = comment.add(T_PROJ_ID, T_REF, T_AUTHOR, T_CONTENT)
        assert cid1
        cid2 = comment.add(T_PROJ_ID, T_REF, T_AUTHOR, T_CONTENT)
        assert cid2
        assert cid1 != cid2

    def test_get_comment(self):
        cid = comment.add(T_PROJ_ID, T_REF, T_AUTHOR, T_CONTENT)
        com = comment.get(cid)
        assert com[1] == T_PROJ_ID
        assert com[2] == T_REF

    def test_chinese_comment(self):
        T_CONTENT_ZH = 'test is 牛B'
        cid = comment.add(T_PROJ_ID, T_REF, T_AUTHOR, T_CONTENT_ZH)
        com = comment.get(cid)
        assert com[4] == T_CONTENT_ZH

    def test_get_unexisting_comment(self):
        cid = comment.add(T_PROJ_ID, T_REF, T_AUTHOR, T_CONTENT)
        com = comment.get(cid + 1)
        assert com is None

    def test_delete_comment(self):
        cid = comment.add(T_PROJ_ID, T_REF, T_AUTHOR, T_CONTENT)
        assert comment.get(cid)
        ok = comment.delete(cid)
        assert ok
        assert not comment.get(cid)
        assert not comment.delete(cid), "Cannot delete twice same comment"

    def test_gets_by_project_id(self):
        cid1 = comment.add(T_PROJ_ID, T_REF, T_AUTHOR, T_CONTENT)
        comment.add(T_PROJ_ID_2, T_REF, T_AUTHOR, T_CONTENT)
        cid2 = comment.add(T_PROJ_ID, T_REF, T_AUTHOR, T_CONTENT2)
        cmnts = comment.gets_by_project(T_PROJ_ID, order='desc')[:2]
        assert cmnts == [cid2, cid1]

    def test_gets_by_ref(self):
        cid1 = comment.add(T_PROJ_ID, T_REF, T_AUTHOR, T_CONTENT)
        comment.add(T_PROJ_ID, T_REF_2, T_AUTHOR, T_CONTENT)
        cid2 = comment.add(T_PROJ_ID, T_REF, T_AUTHOR, T_CONTENT2)
        cmnts = comment.gets_by_ref(T_REF, order='desc')[:2]
        assert cmnts == [cid2, cid1]

    def test_gets_by_proj_and_ref(self):
        cid1 = comment.add(T_PROJ_ID, T_REF, T_AUTHOR, T_CONTENT)
        comment.add(T_PROJ_ID, T_REF_2, T_AUTHOR, T_CONTENT)
        cid2 = comment.add(T_PROJ_ID, T_REF, T_AUTHOR, T_CONTENT2)
        cmnts = comment.gets_by_proj_and_ref(
            T_PROJ_ID, T_REF, order='desc')[:2]
        assert cmnts == [cid2, cid1]

    def test_gets_with_order(self):
        all_cmnts = [comment.add(T_PROJ_ID, T_REF, T_AUTHOR, T_CONTENT)
                     for i in range(30)]
        assert len(all_cmnts) == 30
        assert comment.gets_by_ref(
            T_REF, order='desc')[:30] == list(reversed(all_cmnts))

    def test_gets_with_proj_with_order(self):
        all_cmnts = [comment.add(T_PROJ_ID, T_REF, T_AUTHOR, T_CONTENT)
                     for i in range(30)]
        assert len(all_cmnts) == 30
        assert comment.gets_by_proj_and_ref(
            T_PROJ_ID, T_REF, order='desc')[:30] == list(reversed(all_cmnts))
        assert comment.gets_by_proj_and_ref(
            T_PROJ_ID, T_REF, start=10, limit=5, order='desc') == all_cmnts[15:20][::-1]  # noqa

    def test_modify_comment(self):
        cid = comment.add(T_PROJ_ID, T_REF, T_AUTHOR, T_CONTENT)
        comment.update(cid, {'content': 'new content'})
        assert comment.get(cid)[4] == 'new content'

cC = comment.Comment


class TestCommentORM(TestCase):
    def _add(self, project_id=T_PROJ_ID, ref=T_REF,
             author=T_AUTHOR, content=T_CONTENT):
        return cC.get(comment.add(project_id, ref, author, content))

    def test_add(self):
        c = self._add(T_PROJ_ID, T_REF, T_AUTHOR, T_CONTENT)
        assert c.project_id == T_PROJ_ID
        assert c.ref == T_REF
        assert c.author == T_AUTHOR

    def test_get(self):
        c1 = self._add()
        c2 = cC.get(c1.comment_id)
        assert c1.comment_id == c2.comment_id
        assert c1 == c2

    def test_delete(self):
        c = self._add()
        assert cC.get(c.comment_id)
        ok = cC.delete(c.comment_id)
        assert ok
        assert not cC.get(c.comment_id)

    def test_update(self):
        c = self._add(content='content1')
        assert c.content == 'content1'
        assert cC.get(c.comment_id).content == 'content1'
        c.update('content2')
        assert c.content == 'content2'
        assert cC.get(c.comment_id).content == 'content2'

    def test_gets_by_project_id(self):
        c1 = self._add(T_PROJ_ID)
        self._add(T_PROJ_ID_2)
        c2 = self._add(T_PROJ_ID)
        clist = cC.gets_by_project(T_PROJ_ID, order='desc')[:2]
        assert clist == [c2, c1]
