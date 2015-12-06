# -*- coding: utf-8 -*-

from vilya.libs.store import store


def get_all_ticket():
    rs = store.execute("select id,  closed from codedouban_ticket")
    return rs


def get_ticket_comment_count():
    rs = store.execute("select count(id) from codedouban_ticket_comment")
    return rs[0][0]


def get_all_issue():
    rs = store.execute("select id, closer_id  from issues")
    return rs


def get_issue_comment_count():
    rs = store.execute("select count(id) from issue_comments")
    return rs[0][0]


def get_all_project():
    rs = store.execute("select project_id, fork_from from codedouban_projects")
    return rs


def get_all_gist():
    rs = store.execute("select id, fork_from from gists")
    return rs
