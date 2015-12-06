# -*- coding: utf-8 -*-

from vilya.libs.store import store

from vilya.models.ticket import TicketCodereview, TicketNode
from vilya.models.line_comment import LineComment
from vilya.models.linecomment import CommitLineComment, PullLineComment
from vilya.models.consts import (
    LINECOMMENT_INDEX_EMPTY, LINECOMMENT_INDEX_INVALID,
    LINECOMMENT_TYPE_COMMIT, LINECOMMENT_TYPE_PULL,
    TICKET_NODE_TYPE_LINECOMMENT)

# plz backup table ticket_nodes first.
#  >> create table ticket_nodes_bak as (select * from ticket_nodes);

EMPTY_TO_SHA = ''
EMPTY_OIDS = ''


def clear_all_linecomment_nodes():
    ''' 清空新的 ticket_nodes 数据 '''
    print '## run clear_all_linecomment_nodes'
    store.execute("delete from ticket_nodes "
                  "where type=%s", TICKET_NODE_TYPE_LINECOMMENT)
    store.commit()


def clear_all_linecomments():
    ''' 清空新表 '''
    print '## run clear_all_linecomments'
    store.execute("delete from codedouban_linecomments_v2 where 1=1")
    store.commit()


def clear():
    ''' 清空新数据 '''
    clear_all_linecomment_nodes()
    clear_all_linecomments()


def migrate_pull_linecomments():
    print '## run migrate_pull_linecomments'
    rs = store.execute("select id "
                       "from codedouban_ticket_codereview")
    for r in rs:
        id, = r
        c = TicketCodereview.get(id)
        print '>>>', c.id, c.ticket_id, c.from_ref, c.content
        PATH = c.path if c.path else ''
        new_c = PullLineComment.add_raw(c.ticket_id,
                                        c.from_ref,
                                        EMPTY_TO_SHA,
                                        PATH,
                                        c.new_path if c.new_path else PATH,
                                        EMPTY_OIDS,
                                        EMPTY_OIDS,
                                        c.old,
                                        c.new,
                                        c.author,
                                        c.content,
                                        c.position,
                                        c.time,
                                        c.time)
        tn = TicketNode.add_codereview(new_c)
        print '>>> INSERT TicketNode', tn.id, tn.type_id, tn.author, tn.ticket_id
    print "migrate_pull_linecomments: %s records" % len(rs)


def migrate_commit_linecomments():
    print '## run migrate_commit_linecomments'
    rs = store.execute("select comment_id "
                       "from codedouban_linecomments")
    for r in rs:
        id, = r
        c = LineComment.get(id)
        print '>>>', c.comment_id, c.project_id, c.ref, c.content
        PATH = c.path if c.path else ''
        CommitLineComment.add_raw(c.project_id,
                                  c.ref,
                                  EMPTY_TO_SHA,
                                  PATH,
                                  PATH,
                                  EMPTY_OIDS,
                                  EMPTY_OIDS,
                                  LINECOMMENT_INDEX_INVALID,  # commit linecomment老数据并没有记录linenum
                                  LINECOMMENT_INDEX_INVALID,
                                  c.author,
                                  c.content,
                                  c.position,
                                  c.created,
                                  c.created)
    print "migrate_commit_linecomments: %s records" % len(rs)


def main():
    #clear()
    print '========================================'
    rs = store.execute("select id "
                       "from codedouban_linecomments_v2")
    cnt_before = len(rs)

    print 'migrate start...'
    migrate_pull_linecomments()
    migrate_commit_linecomments()
    print 'migrate end...'

    rs = store.execute("select id "
                       "from codedouban_linecomments_v2")
    cnt_after = len(rs)
    print 'inserted %s records into codedouban_linecomments_v2' % (cnt_after - cnt_before)
    print '========================================'

if __name__ == '__main__':
    main()
