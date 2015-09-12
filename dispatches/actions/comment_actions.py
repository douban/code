#!/usr/bin/env python
# encoding: utf-8

from vilya.config import DOMAIN
from vilya.models.project import CodeDoubanProject
from vilya.models.ticket import Ticket

COMMENT_TEMPLATE = "{content} \n commented on [{sha}]" \
    "({domain}/{proj}/commit/{sha}#{anchor})"


def __enter__(data):
    type_ = data.get('type')
    comment = data.get('comment')
    commit_author = data.get('commit_author')

    comment_dict = dict(ref=comment.ref,
                        author=comment.author,
                        content=comment.content,
                        project_id=comment.project_id,
                        comment_uid=comment.uid)

    rdata = {
        'type': type_,
        'comment': comment_dict,
        'commit_author': commit_author,
    }

    return rdata


def async_comment_to_pr(data):
    ''' commit comment rewrite to pr '''
    type_ = data.get('type')
    if type_ not in ('commit_comment', 'commit_linecomment'):
        return

    comment = data.get('comment')
    ref = comment.get('ref')
    author = comment.get('author')
    content = comment.get('content')
    proj_id = comment.get('project_id')
    comment_uid = comment.get('comment_uid')
    proj = CodeDoubanProject.get(proj_id)
    prs = proj.open_family_pulls
    anchor = comment_uid

    for pr in prs:
        if ref in pr.get_commits_shas():
            content = COMMENT_TEMPLATE.format(content=content,
                                              domain=DOMAIN,
                                              proj=proj.name,
                                              sha=ref,
                                              anchor=anchor)
            ticket = Ticket.get_by_projectid_and_ticketnumber(
                pr.to_proj.id, pr.ticket_id)
            ticket.add_comment(content, author)
