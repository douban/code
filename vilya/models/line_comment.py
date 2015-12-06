# -*- coding: utf-8 -*-
from vilya.libs.store import store, bdb
from vilya.models.consts import LINECOMMENT_INDEX_EMPTY

BDB_COMMIT_LINECOMMENT_CONTENT_KEY = 'commit_linecomment_content:%s'


class LineComment(object):
    # TODO: ! 迁移数据 codedouban_linecomments

    def __init__(self, comment_id, project_id, ref, path, position, author,
                 created, content):
        self.comment_id = comment_id
        self.project_id = project_id
        self.ref = ref
        self.path = path
        self.position = position

        # TODO: 跟 pull linecomment 统一
        self.old = LINECOMMENT_INDEX_EMPTY
        self.new = LINECOMMENT_INDEX_EMPTY
        self.author = author
        bdb_content = bdb.get(BDB_COMMIT_LINECOMMENT_CONTENT_KEY % comment_id)
        self.content = bdb_content or content
        self.created = created

    @property
    def linenum(self):
        return (self.old, self.new)

    # TODO: 重构底层数据后改掉
    @property
    def type(self):
        return 'commit'

    # no use
    def to_dict(self):
        return self.__dict__

    @classmethod
    def add(cls, project_id, ref, path, position, author, content):
        comment_id = store.execute(
            "insert into codedouban_linecomments "
            "(project_id, ref, path, position, author, content) "
            "values (%s, %s, %s, %s, %s, %s)",
            (project_id, ref, path, position, author, content))
        if not comment_id:
            store.rollback()
            raise Exception("Unable to insert new comment")
        store.commit()
        bdb.set(BDB_COMMIT_LINECOMMENT_CONTENT_KEY % comment_id, content)
        return cls.get(comment_id)

    @classmethod
    def get(cls, comment_id):
        rs = store.execute("select comment_id, project_id, ref, path, "
                           "position, author, created, content "
                           "from codedouban_linecomments "
                           "where comment_id = %s", (comment_id,))
        res = rs and rs[0]
        return cls(*res) if res else None

    @classmethod
    def gets_by_proj_and_ref(cls, proj_id, ref):
        rs = store.execute("select comment_id, project_id, ref, path, "
                           "position, author, created, content "
                           "from codedouban_linecomments "
                           "where ref=%s and project_id=%s", (ref, proj_id))
        return [cls(*res) for res in rs]

    def delete(self):
        n = store.execute("delete from codedouban_linecomments "
                          "where comment_id = %s", (self.comment_id,))
        if n:
            store.commit()
            return True
