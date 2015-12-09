# -*- coding: utf-8 -*-

from __future__ import absolute_import

from datetime import datetime
from itertools import groupby

from vilya.libs.store import store, mc, cache, bdb
from vilya.libs.signals import codereview_signal
from dispatches import dispatch
from vilya.libs.props import PropsMixin
from vilya.models.user import User
from vilya.models.project import CodeDoubanProject
from vilya.models.consts import (
    LINECOMMENT_INDEX_EMPTY, TICKET_NODE_TYPE_COMMENT,
    TICKET_NODE_TYPE_LINECOMMENT)
from vilya.models.linecomment import PullLineComment
from vilya.models.nticket import TicketNode, TicketCommits, TicketComment

MCKEY_TICKET = 'ticket:%s'
BDB_TICKET_DESCRIPTION_KEY = 'ticket_description:%s'
BDB_TICKET_LINECOMMENT_CONTENT_KEY = 'ticket_linecomment_content:%s'

TIME_SECOND_TO_MONTH = 2592000
TIME_SECOND_TO_DAY = 86400


class PRCounter(object):

    @classmethod
    def incr(cls, proj_id, count=None):
        if count >= 0:
            sql = ("insert into pullreq_counter (project_id, counter) "
                   "values (%s, LAST_INSERT_ID(%s)) on duplicate key "
                   "update counter = LAST_INSERT_ID(%s)")
            id = store.execute(sql, (proj_id, count, count))
        else:
            sql = ("insert into pullreq_counter (project_id, counter) "
                   "values (%s, LAST_INSERT_ID(%s)) on duplicate key "
                   "update counter = LAST_INSERT_ID(counter + 1)")
            id = store.execute(sql, (proj_id, 1))
        store.commit()
        return id


class Ticket(PropsMixin):

    def __init__(self, id, ticket_number, project_id,
                 title, description, author, time, closed):
        self.id = id
        self.ticket_number = ticket_number  # start from #1 in each project
        self.project_id = project_id
        self.title = title
        bdb_description = bdb.get(BDB_TICKET_DESCRIPTION_KEY % id)
        self.description = bdb_description or description
        self.author = author
        self.time = time
        self.closed = closed

    def get_uuid(self):
        return '/ticket/%s' % self.id

    @property
    def owner(self):
        return User(self.author)

    @property
    def ticket_id(self):
        return self.ticket_number

    @property
    def url(self):
        project = self.project
        if project:
            return '/%s/pull/%s/' % (project.name, self.ticket_number)
        else:
            return ''

    def _get_closed_by(self):
        """
        ticket is closed by whom
        """
        return self.props.get('close_by')

    def _set_closed_by(self, close_by):
        self.set_props_item('close_by', close_by)

    close_by = property(_get_closed_by, _set_closed_by)

    @property
    def project(self):
        return CodeDoubanProject.get(self.project_id)

    @property
    def participants(self):
        return self.props.get('participants') or []

    def add_participant(self, username):
        participants = self.participants
        if username and username not in participants:
            participants.append(username)
            self.set_props_item('participants', participants)

            user = User(username)
            user.add_participated_pull_request(self.id)
        return self.participants

    @classmethod
    def add(cls, project_id, title, description, author, ticket_number=None):
        ticket_number = PRCounter.incr(project_id, ticket_number)
        id = store.execute(
            "insert into codedouban_ticket "
            "(ticket_number, project_id, title, description, author) "
            "values (%s, %s, %s, %s, %s)",
            (ticket_number, project_id, title, description, author))
        if not id:
            store.rollback()
            raise Exception("Unable to add")
        store.commit()
        mc.delete(MCKEY_TICKET % id)
        bdb.set(BDB_TICKET_DESCRIPTION_KEY % id, description)
        ticket = cls.get(id)
        ticket.add_participant(author)
        return ticket

    def update(self, title='', description=''):
        store.execute("update codedouban_ticket set title=%s, description=%s "
                      "where id=%s", (title, description, self.id))
        store.commit()
        mc.delete(MCKEY_TICKET % self.id)
        bdb.set(BDB_TICKET_DESCRIPTION_KEY % self.id, description)

    @classmethod
    @cache(MCKEY_TICKET % '{id}')
    def get(cls, id):
        rs = store.execute("select id, ticket_number, project_id, title, "
                           "description, author, time, closed "
                           "from codedouban_ticket where id = %s", (id,))
        res = rs and rs[0]
        return cls(*res) if res else None

    @classmethod
    def get_by_projectid_and_ticketnumber(cls, project_id, ticket_number):
        rs = store.execute("select id, ticket_number, project_id, title, "
                           "description, author, time, closed "
                           "from codedouban_ticket "
                           "where project_id=%s and ticket_number=%s"
                           % (project_id, ticket_number))
        res = rs and rs[0]
        return cls(*res) if res else None

    @classmethod
    def gets(cls, project_id=None, author=None,
             closed=False, date_from=None, date_to=None):
        sql = "select id, ticket_number, project_id, title, description, " \
              "author, time, closed from codedouban_ticket where "
        values = []
        if closed:
            sql = "%s%s " % (sql, "closed is not NULL")
        else:
            sql = "%s%s " % (sql, "closed is NULL")
        if project_id:
            sql = "%s%s " % (sql, "and project_id=%s")
            values.append(project_id)
        if author:
            sql = "%s%s " % (sql, "and author=%s")
            values.append(author)
        if date_from:
            sql = "%s%s " % (sql, "and time>=%s")
            values.append(date_from)
        if date_to:
            sql = "%s%s " % (sql, "and time<%s")
            values.append(date_to)
        sql = "%s%s " % (sql, "order by time desc ")
        rs = store.execute(sql, values)
        return [cls(*r) for r in rs]

    @classmethod
    def gets_by_projectid_and_ticketnumbers(cls, project_id, ticket_numbers):
        tickets = []
        for ticket_num in ticket_numbers:
            ticket = cls.get_by_projectid_and_ticketnumber(
                project_id, ticket_num)
            if ticket:
                tickets.append(ticket)
        return tickets

    @classmethod
    def get_count_by_proj(cls, proj_id, closed=False):
        rs = store.execute("select count(id) from codedouban_ticket "
                           "where project_id=%s "
                           "and closed is {0} ".format(
                               'not NULL' if closed else 'NULL'), (proj_id,))
        res = rs and rs[0]
        return res[0] if res else 0

    @classmethod
    def get_count_by_proj_and_author(cls, proj_id, author, closed=False):
        rs = store.execute("select count(id) from codedouban_ticket "
                           "where project_id=%s "
                           "and author=%s "
                           "and closed is {0}".format(
                               'not NULL' if closed else 'NULL'),
                           (proj_id, author))
        res = rs and rs[0]
        return res[0] if res else 0

    @classmethod
    def gets_by_proj(cls, proj_id, closed=False, limit=25, start=0):
        rs = store.execute("select id, ticket_number, project_id, title, "
                           "description, author, time, closed "
                           "from codedouban_ticket where project_id=%s "
                           "and closed is {0} order by time desc "
                           "limit %s, %s".format(
                               'not NULL' if closed else 'NULL'),
                           (proj_id, start, limit))
        return [cls(*res) for res in rs]

    @classmethod
    def gets_by_proj_and_author(cls, proj_id, author, closed=False, limit=25,
                                start=0):
        rs = store.execute("select id, ticket_number, project_id, title, "
                           "description, author, time, closed "
                           "from codedouban_ticket where project_id=%s "
                           "and author=%s and closed is {0} order by time"
                           " desc limit %s, %s".format(
                               'not NULL' if closed else 'NULL'),
                           (proj_id, author, start, limit))
        return [cls(*res) for res in rs]

    @classmethod
    def gets_by_team_id(cls, team_id, closed=False, limit=25, start=0):
        rs = store.execute("select id, ticket_number, project_id, title, "
                           "description, author, time, closed "
                           "from codedouban_ticket where project_id in "
                           "(select project_id from team_project_relationship "
                           "where team_id=%s) and closed is {0} "
                           "order by time desc limit %s, %s".format(
                               'not NULL' if closed else 'NULL'),
                           (team_id, start, limit))
        return [cls(*res) for res in rs]

    @classmethod
    def get_count_by_proj_id(cls, proj_id):
        rs = store.execute("select count(id) from codedouban_ticket "
                           "where project_id=%s ",
                           (proj_id,))
        return rs[0][0]

    @classmethod
    def get_count_by_team_id(cls, team_id, closed=False):
        rs = store.execute("select count(id) from codedouban_ticket "
                           "where project_id in (select project_id from "
                           "team_project_relationship where team_id=%s) "
                           "and closed is {0} ".format(
                               'not NULL' if closed else 'NULL'),
                           (team_id,))
        return rs[0][0]

    @classmethod
    def gets_all_by_proj(cls, proj_id):
        rs = store.execute("select id, ticket_number, project_id, title, "
                           "description, author, time, closed "
                           "from codedouban_ticket where project_id=%s",
                           (proj_id,))
        return [cls(*res) for res in rs]

    @classmethod
    def gets_by_author(cls, author, closed=False, limit=25, start=0):
        rs = store.execute(
            "select id, ticket_number, project_id, title, "
            "description, author, time, closed "
            "from codedouban_ticket where author=%s and closed is {0} "
            "order by time desc limit %s, %s".format(
                'not NULL' if closed else 'NULL'),
            (author, start, limit))
        return [cls(*r) for r in rs]

    @classmethod
    def gets_ranks_by_author(cls, author, closed=False, limit=25, start=0):
        rs = store.execute(
            "select id, ticket_number, project_id, title, description, "
            "author, time, closed from codedouban_ticket where author=%s"
            "order by rank_score desc limit %s, %s ",
            (author, start, limit))
        return [cls(*r) for r in rs]

    @classmethod
    def gets_all_opened(cls, limit=100, start=0):
        rs = store.execute("select id, ticket_number, project_id, title, "
                           "description, author, time, closed "
                           "from codedouban_ticket where closed is NULL "
                           "order by time desc limit %s, %s",
                           (start, limit))
        return [cls(*res) for res in rs]

    def get_nodes(self):
        return TicketNode.gets_by_ticket_id(self.id)

    def get_codereviews_group(self):
        # FIXME: refactor this
        # group = { linecomment_id: ... }
        group = {}
        codereviews = PullLineComment.gets_by_target(self.id)
        comparer = lambda x: (x.old_path +
                              (str(x.oids) if x.has_oids else x.from_sha) +
                              str(x.linenum if x.has_linenum else x.position))
        codereviews.sort(key=comparer)
        for k, v in groupby(codereviews, key=comparer):
            crs = list(v)
            codereview = crs[0]
            group[codereview.id] = crs  # 相当于缩点了
        return group

    def get_comments(self):
        comments = TicketComment.gets_by_ticketid(self.id)
        return comments

    # 只是用来拿 length
    def get_codereviews(self):
        codereviews = PullLineComment.gets_by_target(self.id)
        return codereviews

    def get_commits(self):
        return TicketCommits.gets_by_ticketid(self.id)

    def add_commits(self, commits, author):
        commit = TicketCommits.add(self.id, commits, author)
        return commit

    def add_comment(self, content, author):
        self.add_participant(author)
        comment = TicketComment.add(self.id, content, author)
        return comment

    # TODO: 修改调用者，修改参数，需要前端修改模版，js等。。
    def add_codereview(self, from_sha, to_sha,
                       old_path, new_path, from_oid, to_oid,
                       old_linenum, new_linenum,
                       author, content):
        new_path = new_path or old_path
        self.add_participant(author)
        codereview = PullLineComment.add(self.id, from_sha, to_sha,
                                         old_path, new_path, from_oid,
                                         to_oid, old_linenum, new_linenum,
                                         author, content)
        TicketNode.add_codereview(codereview)
        return codereview

    def close(self, operator):
        closed_time = datetime.now()
        store.execute("update codedouban_ticket set closed=%s where id=%s",
                      (closed_time, self.id))
        store.commit()
        mc.delete(MCKEY_TICKET % self.id)
        self.close_by = operator

        for paticipant in self.participants:
            # FIXME better interface
            from vilya.models.user import UserPullRequests
            UserPullRequests(paticipant).remove_participated(self.id)
            UserPullRequests(paticipant).remove_invited(self.id)

        self.add_participant(operator)
        TicketNode.add_close(self.id, operator, closed_time)

    def open(self, operator):
        opened_time = datetime.now()
        store.execute("update codedouban_ticket set closed=null where id=%s",
                      (self.id,))
        store.commit()
        mc.delete(MCKEY_TICKET % self.id)
        self.close_by = None
        self.add_participant(operator)
        TicketNode.add_open(self.id, operator, opened_time)

    def as_dict(self):
        dic = {"title": self.title,
               "description": self.description,
               "author": self.author,
               "time": self.time,
               "closed": self.closed,
               "number": self.ticket_number}
        project = self.project
        if project:
            dic["project"] = project.as_dict()
        return dic


# 只用于迁移数据
class TicketCodereview(object):
    # TODO: ! 迁移数据 codedouban_ticket_codereview

    def __init__(self, id, ticket_id, content, path, position,
                 line_mark, from_ref, author, time, new_path=None):
        self.id = id
        self.ticket_id = ticket_id
        bdb_content = bdb.get(BDB_TICKET_LINECOMMENT_CONTENT_KEY % id)
        self.content = bdb_content or content
        self.path = path
        self.position = position
        self._line_mark = line_mark
        self.old = LINECOMMENT_INDEX_EMPTY
        self.new = LINECOMMENT_INDEX_EMPTY
        if len(line_mark.split('|')) > 1:
            old, new = line_mark.split('|')
            self.old = int(old)
            self.new = int(new)
        self.from_ref = from_ref
        self.author = author
        self.time = time
        self.new_path = new_path

    @property
    def linenum(self):
        return (self.old, self.new)

    # TODO: 重构底层数据后改掉
    @property
    def type(self):
        return 'pull'

    @property
    def has_linenum(self):
        ''' 便于区分老数据，没有linenum的只能用position显示 '''
        return self._line_mark != ''

    @property
    def paths(self):
        ''' file paths(old/new) about this linecomment '''
        if self.new_path:
            return [self.path, self.new_path]
        return [self.path]

    @classmethod
    def add(cls, ticket_id, content, path, position,
            old, new, from_ref, author, new_path=None):
        # FIXME: mysql里的content是废的啊，是历史原因么？
        line_mark = str(old) + '|' + str(new)
        id = store.execute("insert into codedouban_ticket_codereview "
                           "(ticket_id, content, path, position, line_mark, "
                           "from_ref, author, new_path) "
                           "values (%s, %s, %s, %s, %s, %s, %s, %s)",
                           (ticket_id, content, path, position, line_mark,
                            from_ref, author, new_path))
        if not id:
            store.rollback()
            raise Exception("Unable to add")
        store.commit()
        bdb.set(BDB_TICKET_LINECOMMENT_CONTENT_KEY % id, content)
        comment = cls.get(id)
        ticket = Ticket.get(ticket_id)
        # TODO: 重构feed之后取消signal发送
        codereview_signal.send(comment, content=content,
                               ticket=Ticket.get(ticket_id),
                               author=author, comment=comment)
        dispatch('codereview', data={
                 'comment': comment,
                 'ticket': ticket,
                 'sender': author,
                 })
        return comment

    def update(self, content):
        store.execute("update codedouban_ticket_codereview "
                      "set time=now() where id=%s", (self.id,))
        store.commit()
        bdb.set(BDB_TICKET_LINECOMMENT_CONTENT_KEY % self.id, content)

    def delete(self):
        node = TicketNode.get_by_codereview(self)
        if node:
            node.delete()
        bdb.delete(BDB_TICKET_LINECOMMENT_CONTENT_KEY % self.id)
        n = store.execute("delete from codedouban_ticket_codereview "
                          "where id=%s", (self.id,))
        if n:
            store.commit()
            return True

    @classmethod
    def get(cls, id):
        rs = store.execute(
            "select id, ticket_id, content, path, position, line_mark, "
            "from_ref, author, time, new_path "
            "from codedouban_ticket_codereview "
            "where id=%s", (id,))
        res = rs and rs[0]
        return cls(*res) if res else None

    @classmethod
    def gets_by_ticketid(cls, ticket_id):
        rs = store.execute(
            "select id, ticket_id, content, path, position, line_mark, "
            "from_ref, author, time, new_path "
            "from codedouban_ticket_codereview "
            "where ticket_id=%s", (ticket_id,))
        return [cls(*res) for res in rs]

    @classmethod
    def gets_by_ticketid_and_ref(cls, ticket_id, from_ref):
        rs = store.execute(
            "select id, ticket_id, content, path, position, line_mark, "
            "from_ref, author, time, new_path "
            "from codedouban_ticket_codereview "
            "where ticket_id=%s and from_ref=%s",
            (ticket_id, from_ref))
        return [cls(*res) for res in rs]


class TicketRank(object):

    @classmethod
    def get_last_created_time(cls, ticket_id):
        rs = store.execute(
            "select MAX(created_at) "
            "from ticket_nodes where ticket_id=%s ", (ticket_id,))
        return rs[0][0] if rs[0][0] else 0

    @classmethod
    def get_node_count(cls, ticket_id, type):
        rs = store.execute("select count(id) "
                           "from ticket_nodes where ticket_id=%s "
                           "and type = %s",
                           (ticket_id, type))
        return int(rs[0][0]) if rs[0][0] else 0

    @classmethod
    def get_line_comment_count(cls, ticket_id):
        r = cls.get_node_count(ticket_id, TICKET_NODE_TYPE_LINECOMMENT)
        return r

    @classmethod
    def get_comment_count(cls, ticket_id):
        r = cls.get_node_count(ticket_id, TICKET_NODE_TYPE_COMMENT)
        return r

    @classmethod
    def get_sum_count(cls, ticket_id):
        r = cls.get_comment_count(ticket_id) + cls.get_line_comment_count(
            ticket_id) * 1.3
        return r

    @classmethod
    def get_rank_by_ticket_id(cls, ticket_id):
        r = store.execute("select rank_score from codedouban_ticket "
                          "where id=%s", (ticket_id,))
        return r

    @classmethod
    def count_ticket_rank(cls, is_closed):
        limit_min = 0
        r_max = store.execute("select count(id) from codedouban_ticket "
                              "where closed is {0}".format(
                                  'not NULL' if is_closed else 'NULL'))
        max_count = int(r_max[0][0])
        while max_count >= limit_min:
            rs = store.execute(
                "select id, time from codedouban_ticket "
                "where closed is {0} limit %s, 50".format(
                    'not NULL' if is_closed else 'NULL'), limit_min)
            for ticket_id, created_time in rs:
                created_difftime = (
                    datetime.now() - created_time).total_seconds()
                exponent = int(created_difftime / TIME_SECOND_TO_MONTH) + 1

                # 选取最近6个月的ticket
                if exponent < 7:
                    updated_time = cls.get_last_created_time(ticket_id)
                    if updated_time == 0:
                        updated_difftime = (
                            datetime.now() - created_time).total_seconds()
                    else:
                        updated_difftime = (
                            datetime.now() - updated_time).total_seconds()
                    time_score = int(updated_difftime / TIME_SECOND_TO_DAY)

                    sum_count = cls.get_sum_count(ticket_id)
                    time_score = (time_score if is_closed else time_score - 5)

                    # 0.9 ^ Ticket创建到现在时间(月数) X Comment的数量
                    #    + 30 - Ticket最近更新到现在的时间(天数)
                    score = 0.9 ** exponent * sum_count + 30 - time_score
                    store.execute("update codedouban_ticket set rank_score=%s "
                                  "where id=%s", (score, ticket_id))
                    store.commit()
            limit_min = limit_min + 50
