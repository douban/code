# -*- coding: utf-8 -*-

from vilya.libs.store import store, bdb
from vilya.models.consts import (
    LINECOMMENT_INDEX_INVALID,
    LINECOMMENT_TYPE_COMMIT, LINECOMMENT_TYPE_PULL,
    COMMIT_LINECOMMENT_UID_PATTERN, PULL_CODEREVIEW_UID_PATTERN)


BDB_LINECOMMENT_CONTENT_KEY = 'linecomment_content:id:%s'


class LineComment(object):
    ''' new linecomment '''
    _target_type = None
    provided_features = []  # Interface

    def __init__(self, id, target_type, target_id, from_sha, to_sha,
                 old_path, new_path, from_oid, to_oid, old_linenum,
                 new_linenum, position, author, created_at, updated_at):
        self.id = id
        self.target_type = target_type
        self.target_id = target_id
        self.from_sha = from_sha
        self.to_sha = to_sha  # diff: to_sha(from_ref) -> from_sha(to_ref)
        self.old_path = old_path.strip()
        self.new_path = new_path.strip()
        self.from_oid = from_oid
        self.to_oid = to_oid
        self.old_linenum = old_linenum
        self.new_linenum = new_linenum
        self.position = position  # 新数据会为None
        self.author = author
        self.content = bdb.get(BDB_LINECOMMENT_CONTENT_KEY % id)
        self.created_at = created_at
        self.updated_at = updated_at

        # 做兼容... comment(commit comment)跟linecomment在dispatch里是一起处理的，兼容属性名...
        self.path = old_path
        self.ref = from_sha
        self.comment_id = id
        self.created = created_at

    @property
    def linenum(self):
        return (self.old_linenum, self.new_linenum)

    @property
    def has_linenum(self):
        ''' 便于区分老数据，没有linenum的只能用position显示 '''
        return self.old_linenum != LINECOMMENT_INDEX_INVALID

    @property
    def has_oids(self):
        ''' 便于区分老数据，没有oids无法针对文件是否修改进行linecomments的过滤 '''
        return '' not in (self.oids)

    @property
    def has_tosha(self):
        ''' 便于区分老数据，老数据只记录from_sha '''
        return self.to_sha != ''

    def provide(self, name):
        '''检查是否提供某功能，即是否提供某接口'''
        return name in self.provided_features

    @property
    def target(self):
        raise NotImplementedError('Subclasses should implement this!')

    @property
    def uid(self):
        raise NotImplementedError('Subclasses should implement this!')

    @property
    def url(self):
        raise NotImplementedError('Subclasses should implement this!')

    @property
    def paths(self):
        ''' file paths(old/new) about this linecomment '''
        if self.new_path != self.old_path:
            return [self.old_path, self.new_path]
        return [self.old_path]

    @property
    def oids(self):
        ''' file oid(old/new) about this linecomment
        (if file not exist, pygit2 returns '0000...'). '''
        return (self.from_oid, self.to_oid)

    # TODO: for migrate_pull_linecomments
    # FIXME: updated_at 可以正常插入吗？
    @classmethod
    def add_raw(cls, target_id, from_sha, to_sha,
                old_path, new_path, from_oid, to_oid, old_linenum, new_linenum,
                author, content, position, created_at, updated_at):
        id = store.execute(
            "insert into codedouban_linecomments_v2 "
            "(target_type, target_id, from_sha, to_sha, "
            "old_path, new_path, from_oid, to_oid, old_linenum, new_linenum, "
            "author, content, position, created_at, updated_at) "
            "values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",  # noqa
            (cls._target_type, target_id, from_sha, to_sha,
             old_path, new_path, from_oid, to_oid, old_linenum, new_linenum,
             author, content, position, created_at, updated_at))
        if not id:
            store.rollback()
            raise Exception("Unable to add new linecomment")
        store.commit()
        bdb.set(BDB_LINECOMMENT_CONTENT_KEY % id, content)
        return cls.get(id)

    # TODO: LINECOMMENT_INDEX_EMPTY
    @classmethod
    def add(cls, target_id, from_sha, to_sha,
            old_path, new_path, from_oid, to_oid, old_linenum, new_linenum,
            author, content):
        id = store.execute(
            "insert into codedouban_linecomments_v2 "
            "(target_type, target_id, from_sha, to_sha, "
            "old_path, new_path, from_oid, to_oid, old_linenum, new_linenum, "
            "author, content, created_at, updated_at) "
            "values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NULL, NULL)",  # noqa
            (cls._target_type, target_id, from_sha, to_sha,
             old_path, new_path, from_oid, to_oid, old_linenum, new_linenum,
             author, content))
        if not id:
            store.rollback()
            raise Exception("Unable to add new linecomment")
        store.commit()
        bdb.set(BDB_LINECOMMENT_CONTENT_KEY % id, content)
        return cls.get(id)

    @classmethod
    def get(cls, id):
        rs = store.execute(
            "select id, target_type, target_id, from_sha, to_sha, "
            "old_path, new_path, from_oid, to_oid, old_linenum, new_linenum, "
            "position, author, created_at, updated_at "
            "from codedouban_linecomments_v2 "
            "where id = %s", (id,))
        res = rs and rs[0]
        return cls(*res) if res else None

    @classmethod
    def gets_by_target_and_ref(cls, target_id, ref):
        rs = store.execute(
            "select id, target_type, target_id, from_sha, to_sha, "
            "old_path, new_path, from_oid, to_oid, old_linenum, new_linenum, "
            "position, author, created_at, updated_at "
            "from codedouban_linecomments_v2 "
            "where target_type=%s and target_id=%s and from_sha=%s",
            (cls._target_type, target_id, ref))
        return [cls(*res) for res in rs]

    def update(self, content):
        store.execute("update codedouban_linecomments_v2 "
                      "set updated_at=now() where id=%s", (self.id,))
        store.commit()
        bdb.set(BDB_LINECOMMENT_CONTENT_KEY % self.id, content)

    def delete(self):
        n = store.execute("delete from codedouban_linecomments_v2 "
                          "where id = %s", (self.id,))
        if n:
            store.commit()
            return True
        return False

    @classmethod
    def delete_multi(cls, cs):
        for c in cs:
            c.delete()


class CommitLineComment(LineComment):
    _target_type = LINECOMMENT_TYPE_COMMIT
    provided_features = []  # Interface

    @property
    def target(self):
        from vilya.models.project import CodeDoubanProject
        return CodeDoubanProject.get(self.target_id)

    @property
    def project(self):
        return self.target

    @property
    def uid(self):
        return COMMIT_LINECOMMENT_UID_PATTERN % self.id

    @property
    def url(self):
        return '/%s/line_comments/%s/' % (self.project.name, self.id)

    @property
    def project_id(self):
        return self.target_id

    # 做兼容... comment(commit comment)跟linecomment在dispatch里是一起处理的，兼容comment的名字...
    def gets_by_proj_and_ref(self, *k, **kw):
        return self.gets_by_target_and_ref(*k, **kw)


class PullLineComment(LineComment):
    _target_type = LINECOMMENT_TYPE_PULL
    provided_features = ['edit']  # Interface

    @property
    def target(self):
        from vilya.models.ticket import Ticket
        return Ticket.get(self.target_id)

    @property
    def project(self):
        from vilya.models.project import CodeDoubanProject
        return CodeDoubanProject.get(self.target.project_id)

    @property
    def uid(self):
        return PULL_CODEREVIEW_UID_PATTERN % self.id

    @property
    def url(self):
        return '/%s/code_review/%s/' % (self.project.name, self.id)

    @property
    def ticket_id(self):
        return self.target_id

    @classmethod
    def add(cls, target_id, from_sha, to_sha,
            old_path, new_path, from_oid, to_oid, old_linenum, new_linenum,
            author, content):
        # TODO: dispatch 放到 view 里
        from vilya.models.ticket import Ticket
        from vilya.libs.signals import codereview_signal
        from dispatches import dispatch
        comment = super(PullLineComment, cls).add(
            target_id, from_sha, to_sha, old_path, new_path, from_oid,
            to_oid, old_linenum, new_linenum, author, content)
        ticket = Ticket.get(target_id)
        # TODO: 重构feed之后取消signal发送
        if ticket:
            codereview_signal.send(comment, content=content,
                                   ticket=ticket,
                                   author=author, comment=comment)
            dispatch('codereview', data={
                     'comment': comment,
                     'ticket': ticket,
                     'sender': author,
                     })
        return comment

    @classmethod
    def gets_by_target(cls, target_id):
        rs = store.execute(
            "select id, target_type, target_id, from_sha, to_sha, "
            "old_path, new_path, from_oid, to_oid, old_linenum, new_linenum, "
            "position, author, created_at, updated_at "
            "from codedouban_linecomments_v2 "
            "where target_type=%s and target_id=%s",
            (cls._target_type, target_id))
        return [cls(*res) for res in rs]
