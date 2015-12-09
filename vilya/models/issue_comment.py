# -*- coding: utf-8 -*-

from __future__ import absolute_import
from datetime import datetime

from vilya.libs.store import store, mc, cache, bdb

MC_KEY_ISSUE_COMMENTS_COUNT = 'issue_comment_count:v3:%s'
BDB_ISSUE_COMMENT_CONTENT_KEY = 'issue_comment_content:%s'


class ICCounter(object):
    """Issue Comment Counter"""

    @classmethod
    def incr(cls, issue_id, count=None):
        if count >= 0:
            sql = ("insert into issue_comment_counters (issue_id, counter) "
                   "values (%s, LAST_INSERT_ID(%s)) on duplicate key "
                   "update counter = LAST_INSERT_ID(%s)")
            id = store.execute(sql, (issue_id, count, count))
        else:
            sql = ("insert into issue_comment_counters (issue_id, counter) "
                   "values (%s, LAST_INSERT_ID(%s)) on duplicate key "
                   "update counter = LAST_INSERT_ID(counter + 1)")
            id = store.execute(sql, (issue_id, 1))
        store.commit()
        return id


class IssueComment(object):

    def __init__(self, id, issue_id, author, number, created_at=None,
                 updated_at=None):
        self.id = id
        self.issue_id = issue_id
        bdb_content = bdb.get(BDB_ISSUE_COMMENT_CONTENT_KEY % id)
        self.content = bdb_content
        self.author_id = author
        self.number = number
        self.created_at = created_at
        self.updated_at = updated_at

    def __repr__(self):
        return '<IssueComment(id=%s, issue_id=%s)>' % (self.id, self.issue_id)

    @property
    def url(self):
        return '%sissue_comments/%s/' % (self.issue.target.url, self.id)

    @property
    def issue(self):
        from vilya.models.issue import Issue
        return Issue.get_cached_issue(self.issue_id)

    def delete(self):
        bdb.delete(BDB_ISSUE_COMMENT_CONTENT_KEY % self.id)
        n = store.execute("delete from issue_comments "
                          "where id=%s", (self.id,))
        if n:
            store.commit()
            mc.delete(MC_KEY_ISSUE_COMMENTS_COUNT % self.issue_id)
            return True

    @classmethod
    def add(cls, issue_id, content, author_id, number=None):
        number = ICCounter.incr(issue_id, number)
        time = datetime.now()
        comment_id = store.execute(
            'insert into issue_comments (issue_id, author_id, number, '
            'created_at, updated_at) values (%s, %s, %s, NULL, NULL)',
            (issue_id, author_id, number))
        store.commit()
        bdb.set(BDB_ISSUE_COMMENT_CONTENT_KEY % comment_id, content)
        mc.delete(MC_KEY_ISSUE_COMMENTS_COUNT % issue_id)
        return cls(comment_id, issue_id, author_id, number, time, time)

    def as_dict(self):
        d = {}
        d['number'] = self.number
        d['content'] = bdb.get(BDB_ISSUE_COMMENT_CONTENT_KEY % self.id)
        d['author'] = self.author_id
        d['created_at'] = self.created_at.strftime('%Y-%m-%dT%H:%M:%S')
        if self.updated_at:
            d['updated_at'] = self.updated_at.strftime('%Y-%m-%dT%H:%M:%S')
        return d

    @classmethod
    def get(cls, comment_id):
        sql = ("select id, issue_id, author_id, number, created_at, "
               "updated_at from issue_comments where id = %s ")
        rs = store.execute(sql, (comment_id,))
        if rs and rs[0]:
            return cls(*rs[0])

    @classmethod
    def get_by_issue_id_and_number(cls, issue_id, number):
        sql = ("select id, issue_id, author_id, number, created_at, "
               "updated_at from issue_comments where issue_id = %s "
               "and number=%s")
        rs = store.execute(sql, (issue_id, number))
        if rs and rs[0]:
            return cls(*rs[0])

    def update(self, content):
        store.execute("update issue_comments "
                      "set updated_at=CURRENT_TIMESTAMP "
                      "where id=%s", (self.id))
        store.commit()
        bdb.set(BDB_ISSUE_COMMENT_CONTENT_KEY % self.id, content)

    @classmethod
    def gets_by_issue_id(cls, id):
        rs = store.execute("select id, issue_id, "
                           "author_id, number, "
                           "created_at, updated_at "
                           "from issue_comments "
                           "where issue_id=%s ",
                           (id,))
        return [cls(*r) for r in rs]

    @classmethod
    @cache(MC_KEY_ISSUE_COMMENTS_COUNT % '{issue_id}')
    def count_by_issue_id(cls, issue_id):
        rs = store.execute(
            "select count(id) from issue_comments "
            "where issue_id=%s ",
            (issue_id,))
        res = rs and rs[0]
        return res[0] if res else 0
