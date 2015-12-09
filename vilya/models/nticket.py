# -*- coding: utf-8 -*-
from datetime import datetime

from dispatches import dispatch
from vilya.config import DOMAIN
from vilya.libs.store import bdb
from vilya.libs.model import BaseModel, ModelField
from vilya.libs.signals import codereview_signal
from vilya.models.project import CodeDoubanProject
from vilya.models.consts import (
    TICKET_NODE_TYPE_OPEN, TICKET_NODE_TYPE_CLOSE,
    TICKET_NODE_TYPE_MERGE, TICKET_NODE_TYPE_COMMIT,
    TICKET_NODE_TYPE_COMMENT, TICKET_NODE_TYPE_LINECOMMENT,
    PULL_COMMENT_UID_PATTERN)
from vilya.models.linecomment import PullLineComment

BDB_TICKET_COMMENT_CONTENT_KEY = 'ticket_comment_content:%s'


class TicketNode(BaseModel):
    __orz_table__ = "ticket_nodes"
    author = ModelField()
    type = ModelField(as_key=ModelField.KeyType.DESC)
    type_id = ModelField(as_key=ModelField.KeyType.DESC)
    ticket_id = ModelField(as_key=ModelField.KeyType.DESC)
    created_at = ModelField(as_key=ModelField.KeyType.ASC,
                            auto_now_create=True)

    class OrzMeta:
        id2str = False
        order_combs = (("created_at", ),)

    @property
    def commit(self):
        if self.type == TICKET_NODE_TYPE_COMMIT:
            return TicketCommits.get(id=self.type_id)

    @property
    def comment(self):
        if self.type == TICKET_NODE_TYPE_COMMENT:
            return TicketComment.get(id=self.type_id)

    @property
    def codereview(self):
        if self.type == TICKET_NODE_TYPE_LINECOMMENT:
            return PullLineComment.get(self.type_id)

    @classmethod
    def gets_by_ticket_id(cls, id):
        return cls.gets(ticket_id=id, order_by='created_at')

    @classmethod
    def get_by_type_id(cls, type, id):
        return cls.get(type=type, type_id=id)

    @classmethod
    def add(cls, type, type_id, author, ticket_id, created_at):
        return cls.create(type=type,
                          type_id=type_id,
                          author=author,
                          ticket_id=ticket_id,
                          created_at=created_at)

    @classmethod
    def add_commit(cls, commit):
        id = commit.id
        ticket_id = commit.ticket_id
        author = commit.author
        created_at = commit.time
        type = TICKET_NODE_TYPE_COMMIT
        return cls.add(type, id, author, ticket_id, created_at)

    @classmethod
    def add_comment(cls, comment):
        id = comment.id
        ticket_id = comment.ticket_id
        author = comment.author
        created_at = comment.time
        type = TICKET_NODE_TYPE_COMMENT
        return cls.add(type, id, author, ticket_id, created_at)

    @classmethod
    def add_codereview(cls, codereview):
        id = codereview.id
        ticket_id = codereview.target_id
        author = codereview.author
        created_at = codereview.created_at
        type = TICKET_NODE_TYPE_LINECOMMENT
        return cls.add(type, id, author, ticket_id, created_at)

    @classmethod
    def add_merge(cls, ticket_id, author, created_at):
        type = TICKET_NODE_TYPE_MERGE
        id = 0
        return cls.add(type, id, author, ticket_id, created_at)

    @classmethod
    def add_open(cls, ticket_id, author, created_at):
        type = TICKET_NODE_TYPE_OPEN
        id = 0
        return cls.add(type, id, author, ticket_id, created_at)

    @classmethod
    def add_close(cls, ticket_id, author, created_at):
        type = TICKET_NODE_TYPE_CLOSE
        id = 0
        return cls.add(type, id, author, ticket_id, created_at)

    @classmethod
    def get_by_comment(cls, comment):
        type = TICKET_NODE_TYPE_COMMENT
        return cls.get_by_type_id(type, comment.id)

    @classmethod
    def get_by_codereview(cls, codereview):
        type = TICKET_NODE_TYPE_LINECOMMENT
        return cls.get_by_type_id(type, codereview.id)

    # 用于migrate
    @classmethod
    def get_by_codereview_id(cls, codereview_id):
        type = TICKET_NODE_TYPE_LINECOMMENT
        return cls.get_by_type_id(type, codereview_id)

    @classmethod
    def get_by_commit(cls, commit):
        type = TICKET_NODE_TYPE_COMMIT
        return cls.get_by_type_id(type, commit.id)

    def delete_type(self):
        if self.type == TICKET_NODE_TYPE_COMMENT:
            comment = self.comment
            comment.delete()
        elif self.type == TICKET_NODE_TYPE_COMMIT:
            commit = self.commit
            commit.delete()
        elif self.type == TICKET_NODE_TYPE_LINECOMMENT:
            codereview = self.codereview
            codereview.delete()


class TicketCommits(BaseModel):
    __orz_table__ = "codedouban_ticket_commits"
    author = ModelField()
    commits = ModelField()
    ticket_id = ModelField(as_key=ModelField.KeyType.DESC)
    time = ModelField(as_key=ModelField.KeyType.DESC, auto_now_create=True)

    @property
    def ticket(self):
        from vilya.models.ticket import Ticket
        return Ticket.get(self.ticket_id)

    @property
    def project(self):
        return CodeDoubanProject.get(self.ticket.project_id)

    @classmethod
    def commit_as_dict(cls, proj, sha):
        d = {}
        d['sha'] = sha
        commit = proj.repo.get_commit(sha)
        d['commit'] = {}
        d['commit']['html_url'] = "%s/%s/commits/%s" % (
            DOMAIN, proj.name, sha)
        d['commit']['sha'] = sha
        d['commit']['message'] = commit.message
        d['commit']['date'] = commit.committer_time.strftime(
            '%Y-%m-%dT%H:%M:%S')
        d['commit']['author'] = dict(
            name=commit.author.name,
            email=commit.author.email
        )
        d['commit']['committer'] = dict(
            name=commit.committer.name,
            email=commit.committer.email
        )
        d['commit']['tree'] = dict(
            html_url="%s/%s/tree/%s" % (DOMAIN, proj.name, sha),
            sha=sha
        )

        parent = [dict(sha=commit.parent,
                       html_url="%s/%s/commits/%s" % (DOMAIN,
                                                      proj.name,
                                                      commit.parent))
                  ] if commit.parent else []
        d['parent'] = parent

        files = []
        for delta in commit.diff.deltas:
            files.append(dict(type=delta.status_text,
                              filepath=delta.new_file_path))
        d['commit']['files'] = files

        return d

    def as_dict(self):
        l = []
        for sha in self.commits.split(','):
            d = TicketCommits.commit_as_dict(self.project, sha)
            l.append(d)
        return l

    @classmethod
    def add(cls, ticket_id, commits, author):
        return cls.create(ticket_id=ticket_id, commits=commits, author=author)

    @classmethod
    def gets_by_ticketid(cls, ticket_id):
        return cls.gets(ticket_id=ticket_id)

    def after_create(self):
        commit = self
        TicketNode.add_commit(commit)


class TicketComment(BaseModel):
    __orz_table__ = "codedouban_ticket_comment"
    author = ModelField()
    # content = ModelField()
    ticket_id = ModelField(as_key=ModelField.KeyType.DESC)
    time = ModelField(as_key=ModelField.KeyType.DESC, auto_now_create=True)

    @property
    def content(self):
        return bdb.get(BDB_TICKET_COMMENT_CONTENT_KEY % self.id)

    @property
    def uid(self):
        return PULL_COMMENT_UID_PATTERN % self.id

    def as_dict(self):
        return {
            'content': self.content,
            'author': self.author,
            'date': self.time.strftime('%Y-%m-%dT%H:%M:%S'),
            'id': self.id,
            'ticket_id': self.ticket_id
        }

    @classmethod
    def add(cls, ticket_id, content, author):
        comment = cls.create(ticket_id=ticket_id,
                             extra_args=content,
                             author=author)
        return comment

    def after_create(self, extra_args):
        from vilya.models.ticket import Ticket
        comment = self
        TicketNode.add_comment(comment)
        content = extra_args
        bdb.set(BDB_TICKET_COMMENT_CONTENT_KEY % self.id, content)
        ticket = Ticket.get(self.ticket_id)
        # TODO: 将Feed全部迁移到新的系统后，取消signal发送
        codereview_signal.send(comment,
                               content=content,
                               ticket=ticket,
                               author=self.author,
                               comment=comment)
        dispatch('codereview', data={
            'comment': comment,
            'ticket': ticket,
            'sender': self.author,
        })

    def update(self, content):
        bdb.set(BDB_TICKET_COMMENT_CONTENT_KEY % self.id, content)
        self.time = datetime.now()
        self.save()

    def after_delete(self):
        bdb.delete(BDB_TICKET_COMMENT_CONTENT_KEY % self.id)
        node = TicketNode.get_by_comment(self)
        if node:
            node.delete()

    @classmethod
    def gets_by_ticketid(cls, ticket_id):
        return cls.gets(ticket_id=ticket_id)
