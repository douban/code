# -*- coding: utf-8 -*-

from __future__ import absolute_import
import logging
logging.getLogger().setLevel(logging.DEBUG)

from vilya.libs.mlock import MLock
from vilya.models.project import CodeDoubanProject
from vilya.models.ticket import Ticket
from vilya.models.lru_counter import (
    ProjectOwnLRUCounter, ProjectWatchLRUCounter)
from vilya.models.npull import Pull2

# mc keys, ('{self.id}', '{self.from_sha}', '{self.to_sha}')
MC_KEY_PULL_MERGE_BASE = 'PullRequest:%s:%s:%s:merge_base'
MC_KEY_PULL_IS_MERGABLE = 'PullRequest:%s:%s:%s:is_auto_mergable'
MC_KEY_PULL_ID_BY_PID_AND_TID = 'PullRequest:%s:%s:pull_id'

PullRequest = Pull2


def add_pull(ticket, pullreq, user):
    from dispatches import dispatch
    from vilya.libs.text import get_mentions_from_text
    from vilya.libs.signals import pullrequest_signal
    from vilya.models.user import get_author_by_email
    from vilya.models.user import User
    from vilya.models.trello.core import process_trello_notify

    reporter = user.username
    commits = pullreq.commits
    # TODO: refactory is! auto number how to?
    shas = [p.sha for p in commits]
    ticket_len = Ticket.get_count_by_proj_id(ticket.project_id)
    if ticket_len == 0:
        # 检查是否创建过新PR，若未创建过则以旧PR号为基准累加
        max_ticket_id = PullRequest.get_max_ticket_id(ticket.project_id)
        if max_ticket_id >= 0:
            ticket = Ticket.add(ticket.project_id,
                                ticket.title,
                                ticket.description,
                                ticket.author,
                                max_ticket_id + 1)
        else:
            ticket = Ticket.add(ticket.project_id,
                                ticket.title,
                                ticket.description,
                                ticket.author)
    else:
        ticket = Ticket.add(ticket.project_id,
                            ticket.title,
                            ticket.description,
                            ticket.author)
    pullreq = pullreq.insert(ticket.ticket_number)

    if shas:
        ticket.add_commits(','.join(shas), reporter)
    noti_receivers = [committer.name
                      for committer in CodeDoubanProject.get_committers_by_project(pullreq.to_proj.id)]  # noqa
    noti_receivers = noti_receivers + [pullreq.to_proj.owner.name]
    get_commit_author = lambda u: get_author_by_email(u.email.encode('utf-8'))
    commit_authors = {get_commit_author(c.author) for c in commits}
    commit_authors = {a for a in commit_authors if a}
    noti_receivers.extend(commit_authors)

    # diffs, author_by_file, authors = pullreq.get_diffs(with_blame=True)
    # FIXME: diffs没用到?
    # diffs = pullreq.get_diffs()

    # blame代码变更的原作者, 也加到at users
    at_users = get_mentions_from_text(ticket.description)
    # at_users.extend(authors)
    at_users.append(pullreq.to_proj.owner_id)
    at_users = set(at_users)

    # FIXME: invited_users is used on page /hub/my_pull_requests/
    invited_users = [User(u).add_invited_pull_request(ticket.id)
                     for u in at_users]

    ProjectOwnLRUCounter(user.username).use(pullreq.to_proj.id)
    ProjectWatchLRUCounter(user.username).use(pullreq.to_proj.id)

    # TODO: 重构Feed之后取消这个信号的发送
    pullrequest_signal.send(user.username,
                            extra_receivers=noti_receivers,
                            pullreq=pullreq,
                            comment=ticket.description,
                            ticket_id=ticket.ticket_id,
                            ticket=ticket,
                            status="unmerge",
                            new_version=True)

    dispatch('pullreq',
             data=dict(sender=user.username,
                       content=ticket.description,
                       ticket=ticket,
                       status='unmerge',
                       new_version=True,
                       extra_receivers=noti_receivers))

    dispatch('pr_actions',
             data=dict(type='pr_opened',
                       hooks=pullreq.to_proj.hooks,
                       author=user,
                       title=ticket.title,
                       body=ticket.description,
                       ticket=ticket,
                       pullreq=pullreq))

    # FIXME: move to dispatch
    process_trello_notify(user, ticket)
    return pullreq


# TODO: user merge_pull_before() and merge_pull_after()
# TODO: remove argu: request
def merge_pull(ticket, pullreq, user, message, request):
    from dispatches import dispatch
    from queues_handler import sphinx_builds_add
    from vilya.libs.signals import pullrequest_signal
    project = pullreq.to_proj
    # before
    # check user permission
    if not project.has_push_perm(user.name):
        return 'You do not have merge permission'
    # check if pull merged
    if pullreq.merged:
        return 'This pull was already merged'

    with MLock.merge_pull(proj_id=pullreq.to_proj.id) as err:
        if err:
            return "Merging by someone else ..."

        # if up-to-date, just close it
        if pullreq.is_up_to_date():
            content = u"Closed due to up-to-date merge"
            comment = ticket.add_comment(content, user.name)
            close_pull(ticket, pullreq, user, content, comment,
                       request)
            return "Closed due to up-to-date merge"

        # do
        merge_commit_sha = pullreq.merge(user, message)
        if merge_commit_sha is None:
            return "Merge failed"
        # after
        ticket_id = ticket.ticket_id
        # close ticket
        ticket.close(user.name)
        # build docs
        sphinx_builds_add(project.name)
        # delete tmp branch
        pullreq.remove_branch_if_temp()

    # TODO: 重构Feed后取消这个信号的发送
    pullrequest_signal.send(user.username,
                            comment='',
                            pullreq=pullreq,
                            ticket_id=ticket_id,
                            ticket=ticket,
                            status="merged",
                            new_version=True)

    dispatch('pullreq',
             data=dict(sender=user.username,
                       comment=None,
                       ticket=ticket,
                       status='merged',
                       new_version=True)
             )

    # remove argu: request
    dispatch('pr_actions',
             data=dict(type='pr_merge',
                       hooks=project.hooks,
                       request=request,
                       commit_message=message,
                       author=user,
                       ticket=ticket,
                       pullreq=pullreq)
             )
    return None


def close_pull(ticket, pullreq, user, content, comment, request):
    from dispatches import dispatch
    from vilya.libs.signals import pullrequest_signal

    project = ticket.project
    author = user.name
    ticket.close(author)
    pullreq.remove_branch_if_temp()

    # TODO: 重构Feed后取消发送这个信号
    pullrequest_signal.send(author, comment=content,
                            pullreq=pullreq,
                            ticket_id=ticket.ticket_id,
                            ticket=ticket,
                            status="closed", new_version=True)
    dispatch('pullreq', data={
             'sender': author,
             'comment': comment,
             'ticket': ticket,
             'status': 'closed'})
    dispatch('pr_actions',
             data=dict(
                 type='pr_closed',
                 hooks=project.hooks,
                 request=request,
                 author=user,
                 ticket=ticket,
                 pullreq=pullreq,
                 content=content))
