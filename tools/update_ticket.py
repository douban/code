# -*- coding: utf-8 -*-

from vilya.libs.store import store
from vilya.models.consts import (
    TICKET_NODE_TYPE_OPEN, TICKET_NODE_TYPE_CLOSE,
    TICKET_NODE_TYPE_MERGE, TICKET_NODE_TYPE_COMMIT,
    TICKET_NODE_TYPE_COMMENT, TICKET_NODE_TYPE_CODEREVIEW)
from vilya.models.ticket import Ticket
from vilya.models.pull import PullRequest


def get_node(author, type, id, ticket_id, time):
    rs = store.execute("select id, author, type, type_id, ticket_id, created_at "
                       "from ticket_nodes "
                       "where author=%s and type=%s and type_id=%s and ticket_id=%s and created_at=%s",
                       (author, type, id, ticket_id, time))
    if rs and rs[0]:
        return True


def update_commits(from_id=None):
    # update commit
    if from_id:
        rs = store.execute("select id, author, time, ticket_id "
                           "from codedouban_ticket_commits where id > %s",
                           from_id)
    else:
        rs = store.execute("select id, author, time, ticket_id "
                           "from codedouban_ticket_commits")
    for r in rs:
        id, author, time, ticket_id = r
        if not get_node(author, TICKET_NODE_TYPE_COMMIT, id, ticket_id, time):
            print id, author, time, ticket_id
            store.execute("insert into ticket_nodes "
                          "(author, type, type_id, ticket_id, created_at) "
                          "value (%s, %s, %s, %s, %s)",
                          (author, TICKET_NODE_TYPE_COMMIT, id, ticket_id, time))
            store.commit()
    print "update %s commits" % len(rs)


def update_comments(from_id=None):
    # update comment
    if from_id:
        rs = store.execute("select id, author, time, ticket_id "
                           "from codedouban_ticket_comment where id > %s",
                           from_id)
    else:
        rs = store.execute("select id, author, time, ticket_id "
                           "from codedouban_ticket_comment")
    for r in rs:
        id, author, time, ticket_id = r
        print id, author, time, ticket_id
        if not get_node(author, TICKET_NODE_TYPE_COMMENT, id, ticket_id, time):
            print id, author, time, ticket_id
            store.execute("insert into ticket_nodes "
                          "(author, type, type_id, ticket_id, created_at) "
                          "value (%s, %s, %s, %s, %s)",
                          (author, TICKET_NODE_TYPE_COMMENT, id, ticket_id, time))
            store.commit()
    print "update %s comments" % len(rs)


def update_codereviews(from_id=None):
    # update codereview
    if from_id:
        rs = store.execute("select id, author, time, ticket_id "
                           "from codedouban_ticket_codereview where id > %s",
                           from_id)
    else:
        rs = store.execute("select id, author, time, ticket_id "
                           "from codedouban_ticket_codereview")
    for r in rs:
        id, author, time, ticket_id = r
        if not get_node(author, TICKET_NODE_TYPE_CODEREVIEW, id, ticket_id, time):
            print id, author, time, ticket_id
            store.execute("insert into ticket_nodes "
                          "(author, type, type_id, ticket_id, created_at) "
                          "value (%s, %s, %s, %s, %s)",
                          (author, TICKET_NODE_TYPE_CODEREVIEW, id, ticket_id, time))
            store.commit()
    print "update %s reviews" % len(rs)


def main():
    rs = store.execute("select id "
                       "from codedouban_ticket")
    for r in rs:
        id, = r
        ticket = Ticket.get(id)
        # update merge
        pullreq = PullRequest.get_by_ticket(ticket)
        author = pullreq.merge_by or pullreq.to_proj.owner_id
        time = pullreq.merge_time
        ticket_id = ticket.id
        id = 0
        if not get_node(author, TICKET_NODE_TYPE_MERGE, id, ticket_id, time) and time:
            print id, author, time, ticket_id
            store.execute("insert into ticket_nodes "
                          "(author, type, type_id, ticket_id, created_at) "
                          "value (%s, %s, %s, %s, %s)",
                          (author, TICKET_NODE_TYPE_MERGE, id, ticket_id, time))
            store.commit()
        # update close
        author = ticket.close_by or ticket.author
        time = ticket.closed
        ticket_id = ticket.id
        id = 0
        if not get_node(author, TICKET_NODE_TYPE_CLOSE, id, ticket_id, time) and time:
            print id, author, time, ticket_id
            store.execute("insert into ticket_nodes "
                          "(author, type, type_id, ticket_id, created_at) "
                          "value (%s, %s, %s, %s, %s)",
                          (author, TICKET_NODE_TYPE_CLOSE, id, ticket_id, time))
            store.commit()
    print "update %s close & merge pulls" % len(rs)


if __name__ == "__main__":
    main()
