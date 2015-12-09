# -*- coding: utf-8 -*-

import json
import uuid
import re
from datetime import datetime, date
from time import mktime

from vilya.libs.text import trunc_utf8
from vilya.models.consts import DOUBAN_EMAIL


class CJsonEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        else:
            return json.JSONEncoder.default(self, obj)


def linear_normalized(data):
    min_val = min(data or [0, ])
    max_val = max(data or [0, ])
    if min_val == max_val:
        return [0.5 for i in data]
    return [(d - min_val) / (max_val - min_val) for d in data]


def format_pullrequest_info(sender, **kw):
    pullreq = kw['pullreq']
    ticket_id = kw['ticket_id']
    ticket = kw['ticket']
    status = kw['status']
    new_version = kw['new_version']
    type = 'pull_request'

    if new_version:
        ticket_fields = dict(
            reporter=ticket.author,
            description=ticket.description,
            owner=pullreq.merge_by or sender,
            summary=ticket.title
        )
    else:
        ticket_fields = ticket.values
    uid = 'pullrequest-%s-%s-%s' % (pullreq.to_proj, ticket_id, status)

    if new_version:
        pullreq_url = "/%s/pull/%s/" % (
            pullreq.to_proj, ticket.ticket_id)
    else:
        pullreq_url = "/%s/pull/%s/" % (pullreq.to_proj, ticket.id)
    to_proj_str = "%s:%s" % (pullreq.to_proj, pullreq.to_branch)
    from_proj_str = "%s:%s" % (pullreq.from_proj, pullreq.from_branch)
    commiter = ticket_fields['reporter']

    data = dict(
        date=datetime.now(),
        url=pullreq_url,
        description=ticket_fields['description'],
        from_proj=from_proj_str,
        to_proj=to_proj_str,
        commiter=commiter,
        owner=ticket_fields['owner'],
        title=ticket_fields['summary'],
        status=status,
        uid=uid,
        type=type,
    )
    return data


def format_code_review_info(sender, **kw):
    from vilya.models.pull import PullRequest
    comment = kw['comment']
    anchor_id = comment.uid
    ticket = kw['ticket']
    author = kw['author']
    content = kw['content']
    ticket_id = ticket.ticket_id
    pullreq = PullRequest.get_by_ticket(ticket)
    uid = 'newcodereview-%s-%s-%s' % (
        pullreq.to_proj, ticket_id, comment.id)
    type = 'code_review'
    data = dict(
        date=datetime.now(),
        url="/%s/pull/%s/#%s" % (pullreq.to_proj, ticket_id, anchor_id),
        ticket=ticket_id,
        proj="%s:%s" % (pullreq.to_proj, pullreq.to_branch),
        receiver=ticket.author,
        author=author,
        text=content,
        uid=uid,
        type=type,
    )
    return data


def get_target_url(desc):
    '''
    >>> get_target_url('Your browser should have redirected
    you to http://localhost:9640/qingfeng/test/newpull/17/')
    'http://localhost:9640/qingfeng/test/newpull/17/'
    '''
    """aaa http://xxxx"""
    URL_REGEX = re.compile(r"^.+(?P<url>http://.*)$")
    m = re.search(URL_REGEX, desc)
    if m:
        return m.group('url')


def parse_trello_card_code(comment):
    '''
    >>> parse_trello_card_code('https://trello.com/c/HMUQ6Fpc/326-with-at')
    'HMUQ6Fpc'
    >>> parse_trello_card_code('见https://trello.com/c/HMUQ6Fpc/326-with-at')
    'HMUQ6Fpc'
    '''
    """https://trello.com/card/1642297-ume/5105117d52f437bd25002590/95"""
    CARD_REGEX = re.compile(
        r"https://trello.com/c/(?P<card_id>[^\/]+)/[\d\w-]+")
    m = re.search(CARD_REGEX, comment)
    if m:
        return m.group("card_id")


def get_uuid():
    return str(uuid.uuid4())


def get_issue_by_issue_id(issue_id):
    from vilya.models.issue import Issue
    issue = Issue.get_cached_issue(issue_id)
    return issue


def format_issue_info(**kw):
    issue_id = kw['issue_id']
    author = kw['author']
    content = kw['content']

    issue = get_issue_by_issue_id(issue_id)
    target = issue.target

    uid = 'issue-%s-%s-%s' % (issue.target_type, target.id, issue.number)
    text = trunc_utf8(content, 50)
    state = issue.state
    type = 'issue'
    data = dict(
        date=datetime.now(),
        url=issue.url,
        number=issue.number,
        target_name="%s" % target.name,
        target_url="%s" % target.url,
        state=state,
        receiver=issue.creator_id,
        title=issue.title,
        author=author,
        text=text,
        uid=uid,
        type=type,
    )
    return data


def format_issue_comment_info(**kw):
    from vilya.models.issue_comment import IssueComment
    issue_id = kw['issue_id']
    author = kw['author']
    content = kw['content']
    comment_id = kw['comment_id']

    issue = get_issue_by_issue_id(issue_id)
    target = issue.target

    issue_comment = IssueComment.get(comment_id)
    text = trunc_utf8(content, 50)
    uid = "issue-comment-%s-%s-%s-%s" % (
        issue.target_type, target.id, issue.number, issue_comment.number)
    type = 'issue_comment'
    data = dict(
        date=datetime.now(),
        url="%s#comment-%s" % (issue.url, issue_comment.number),
        number=issue.number,
        title=issue.title,
        target_name="%s" % target.name,
        target_url="%s" % target.url,
        receiver=issue.creator_id,
        author=author,
        text=text,
        uid=uid,
        type=type,
    )
    return data


def to_timestamp(date):
    assert isinstance(date, datetime)
    return mktime(date.timetuple())


def check_douban_email(email):
    if not email:
        return False
    for patten in DOUBAN_EMAIL:
        if email.endswith(patten):
            return True
    return False


class _Missing(object):

    def __repr__(self):
        return 'no value'

    def __reduce__(self):
        return '_missing'

_missing = _Missing()


if __name__ == "__main__":
    import doctest
    doctest.testmod()
