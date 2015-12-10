# -*- coding: utf-8 -*-

from tests.base import TestCase

from vilya.models.linecomment import CommitLineComment, PullLineComment
from vilya.models.consts import (
    LINECOMMENT_TYPE_COMMIT, LINECOMMENT_TYPE_PULL)

TARGET_ID = 123
FROM_SHA = '2a200e45b0e223d13477e'
TO_SHA = '2a200e45b0e223d13477e'
OLD_PATH = 'testfolder/testfile.py'
NEW_PATH = 'testfolder/testfile2.py'
FROM_OID = '2a200e45b0e223d13477e'  # TODO: oids
TO_OID = '2a200e45b0e223d13477e'
AUTHOR = 'user1'
CONTENT1 = 'test line comment content'
CONTENT2 = 'another test line comment content'
CONTENT_ZH = u'你好,再见'


class LineCommentTest(TestCase):

    def test_add_comment(self):
        # commit
        c1 = CommitLineComment.add(TARGET_ID, FROM_SHA, TO_SHA,
                                   OLD_PATH, NEW_PATH, FROM_OID, TO_OID,
                                   20, 30, AUTHOR, CONTENT1)
        assert c1.target_id == TARGET_ID
        assert c1.target_type == LINECOMMENT_TYPE_COMMIT
        assert c1.from_sha == FROM_SHA
        assert c1.to_sha == TO_SHA
        assert c1.old_path == OLD_PATH
        assert c1.new_path == NEW_PATH
        assert c1.from_oid == FROM_OID
        assert c1.to_oid == TO_OID
        assert c1.old_linenum == 20
        assert c1.new_linenum == 30
        assert c1.linenum == (20, 30)
        assert c1.author == AUTHOR
        assert c1.content == CONTENT1
        assert c1.position is None
        assert c1.paths

        # pull
        c2 = PullLineComment.add(TARGET_ID, FROM_SHA, TO_SHA,
                                 OLD_PATH, NEW_PATH, FROM_OID, TO_OID,
                                 20, 30, AUTHOR, CONTENT2)
        assert c2.target_id == TARGET_ID
        assert c2.target_type == LINECOMMENT_TYPE_PULL
        assert c2.from_sha == FROM_SHA
        assert c2.to_sha == TO_SHA
        assert c2.old_path == OLD_PATH
        assert c2.new_path == NEW_PATH
        assert c2.from_oid == FROM_OID
        assert c2.to_oid == TO_OID
        assert c2.old_linenum == 20
        assert c2.new_linenum == 30
        assert c2.linenum == (20, 30)
        assert c2.author == AUTHOR
        assert c2.content == CONTENT2
        assert c2.position is None
        assert c2.paths

    def test_update_comment(self):
        # commit
        c1 = CommitLineComment.add(TARGET_ID, FROM_SHA, TO_SHA,
                                   OLD_PATH, NEW_PATH, FROM_OID, TO_OID,
                                   20, 30, AUTHOR, CONTENT1)
        assert c1.content == CONTENT1
        c1.update(CONTENT2)
        c1 = CommitLineComment.get(c1.id)
        assert c1.content == CONTENT2

        # pull
        c2 = PullLineComment.add(TARGET_ID, FROM_SHA, TO_SHA,
                                 OLD_PATH, NEW_PATH, FROM_OID, TO_OID,
                                 20, 30, AUTHOR, CONTENT2)
        assert c2.content == CONTENT2
        c2.update(CONTENT_ZH)
        c2 = CommitLineComment.get(c2.id)
        assert c2.content == CONTENT_ZH

    def test_delete_comment(self):
        # commit
        self.clear_comments(CommitLineComment, TARGET_ID, FROM_SHA)
        c1 = CommitLineComment.add(TARGET_ID, FROM_SHA, TO_SHA,
                                   OLD_PATH, NEW_PATH, FROM_OID, TO_OID,
                                   20, 30, AUTHOR, CONTENT1)
        cs = CommitLineComment.gets_by_target_and_ref(TARGET_ID, FROM_SHA)
        assert len(cs) == 1
        c1.delete()
        cs = CommitLineComment.gets_by_target_and_ref(TARGET_ID, FROM_SHA)
        assert len(cs) == 0

        # pull
        self.clear_comments(PullLineComment, TARGET_ID, FROM_SHA)
        c2 = PullLineComment.add(TARGET_ID, FROM_SHA, TO_SHA,
                                 OLD_PATH, NEW_PATH, FROM_OID, TO_OID,
                                 20, 30, AUTHOR, CONTENT1)
        cs = PullLineComment.gets_by_target_and_ref(TARGET_ID, FROM_SHA)
        assert len(cs) == 1
        c2.delete()
        cs = PullLineComment.gets_by_target_and_ref(TARGET_ID, FROM_SHA)
        assert len(cs) == 0

    def test_gets_by_target_and_ref(self):
        # commit
        self.clear_comments(CommitLineComment, TARGET_ID, FROM_SHA)
        c1 = CommitLineComment.add(TARGET_ID, FROM_SHA, TO_SHA,
                                   OLD_PATH, NEW_PATH, FROM_OID, TO_OID,
                                   20, 30, AUTHOR, CONTENT1)
        c2 = CommitLineComment.add(TARGET_ID, FROM_SHA, TO_SHA,
                                   OLD_PATH, NEW_PATH, FROM_OID, TO_OID,
                                   20, 30, AUTHOR, CONTENT1)
        c3 = CommitLineComment.add(TARGET_ID, FROM_SHA, TO_SHA,
                                   OLD_PATH, NEW_PATH, FROM_OID, TO_OID,
                                   20, 30, AUTHOR, CONTENT1)
        cs = CommitLineComment.gets_by_target_and_ref(TARGET_ID, FROM_SHA)
        assert len(cs) == 3

        self.clear_comments(PullLineComment, TARGET_ID, FROM_SHA)
        # pull
        PullLineComment.add(TARGET_ID, FROM_SHA, TO_SHA,
                            OLD_PATH, NEW_PATH, FROM_OID, TO_OID,
                            20, 30, AUTHOR, CONTENT1)
        PullLineComment.add(TARGET_ID, FROM_SHA, TO_SHA,
                            OLD_PATH, NEW_PATH, FROM_OID, TO_OID,
                            20, 30, AUTHOR, CONTENT1)
        cs = PullLineComment.gets_by_target_and_ref(TARGET_ID, FROM_SHA)
        assert len(cs) == 2

    def clear_comments(self, classObj, TARGET_ID, FROM_SHA):
        cs = classObj.gets_by_target_and_ref(TARGET_ID, FROM_SHA)
        classObj.delete_multi(cs)
