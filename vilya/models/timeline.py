# -*- coding: utf-8 -*-
from __future__ import absolute_import
import logging

from vilya.models.user import User
from vilya.models.pull import PullRequest
from vilya.models.project import CodeDoubanProject
from vilya.models.ticket import Ticket
from vilya.models.comment import Comment
from vilya.models.issue import Issue
from vilya.models.team_issue import TeamIssue
from vilya.models.project_issue import ProjectIssue
from vilya.models.gist import Gist
from vilya.models.team import Team

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _get_user_by_name(name):
    user = {}
    _user = User(name)
    user = dict(
        name=_user.name,
        icon=_user.avatar_url,
    )
    return user


def _get_project_by_name(name):
    project = {}
    _project = CodeDoubanProject.get_by_name(name)
    if not _project:
        return None
    _author = _get_user_by_name(_project.owner_id)
    project = dict(
        id=_project.id,
        name=_project.name,
        owner=_author,
    )
    return project


def _get_project_by_id(id):
    project = {}
    _project = CodeDoubanProject.get(id)
    _author = _get_user_by_name(_project.owner_id)
    project = dict(
        id=_project.id,
        name=_project.name,
        owner=_author,
    )
    return project


def _get_pr_by_project_and_ticket(project, ticket):
    pull = PullRequest.get_by_proj_and_ticket(project.id, ticket.ticket_id)
    _from_project = _get_project_by_name(str(pull.from_proj))
    if _from_project:
        _from_project['branch'] = pull.from_branch
    _to_project = _get_project_by_name(str(pull.to_proj))
    if _to_project:
        _to_project['branch'] = pull.to_branch
    commits = pull.commits
    commit = [_format_commit_object_data(c) for c in commits]
    pr = dict(
        id=ticket.ticket_id,
        name=ticket.title,
        from_project=_from_project,
        to_project=_to_project,
        commit=commit,
    )
    return pr


def _get_pr_by_uid(uid):
    pr = {}
    # uid: pullrequest-project-ticketid-status
    if uid and uid.startswith('pullrequest'):
        fields = uid.split('-')
        if len(fields) != 4:
            return pr
        _, project_name, ticket_number, status = fields
        project = CodeDoubanProject.get_by_name(project_name)
        ticket = Ticket.get_by_projectid_and_ticketnumber(project.id,
                                                          ticket_number)
        pr = _get_pr_by_project_and_ticket(project, ticket)
    return pr


def _get_code_review_by_uid(uid):
    code_review = {}
    if uid and uid.startswith('newcodereview'):
        fields = uid.split('-')
        if len(fields) != 4:
            return code_review
        _, project_name, ticket_number, comment_id = fields
        project = CodeDoubanProject.get_by_name(project_name)
        ticket = Ticket.get_by_projectid_and_ticketnumber(project.id,
                                                          ticket_number)
        pr = _get_pr_by_project_and_ticket(project, ticket)
        comment = Comment.get(comment_id)
        # FIXME: comment type
        code_review = dict(
            id=comment_id,
            type='comment',
            pr=pr,
        )
    return code_review


def _get_issue_by_project_and_number(id, number):
    issue = {}
    project_issue = ProjectIssue.get(id, number=number)
    _issue = Issue.get_cached_issue(project_issue.issue_id)
    _author = _get_user_by_name(_issue.creator_id)
    _closer = _get_user_by_name(_issue.closer_id) if _issue.closer_id else {}
    issue = dict(
        id=_issue.issue_id,
        name=_issue.title,
        author=_author,
        closer=_closer,
    )
    return issue


def _get_gist_by_id(id):
    gist = {}
    _gist = Gist.get(id)
    if not _gist:
        return gist
    _owner = _get_user_by_name(_gist.owner_id)
    gist = dict(
        id=_gist.id,
        name=_gist.name,
        owner=_owner,
    )
    if _gist.fork_from:
        _from_gist = Gist.get(_gist.fork_from)
        _owner = _get_user_by_name(_from_gist.owner_id)
        gist['from_gist'] = dict(
            id=_from_gist.id,
            name=_from_gist.name,
            owner=_owner,
        )
    return gist


def _get_gist_by_uid(uid):
    gist = {}
    if uid and uid.startswith('gist'):
        fields = uid.split('-')
        if uid.startswith('gist-create'):
            if len(fields) != 3:
                return gist
            _, _, id = fields
        elif uid.startswith('gist-star'):
            if len(fields) != 4:
                return gist
            _, _, id, author = fields
        elif uid.startswith('gist-fork'):
            if len(fields) != 4:
                return gist
            _, _, from_id, id = fields
        elif uid.startswith('gist-update'):
            if len(fields) != 3:
                return gist
            _, _, id = fields
        elif uid.startswith('gist-comment'):
            if len(fields) != 3:
                return gist
            _, _, id = fields
        gist = _get_gist_by_id(id)
    return gist


def _get_team_by_uid(uid):
    _team = Team.get_by_uid(uid)
    team = dict(
        id=_team.id,
        uid=_team.uid,
        name=_team.name,
    )
    return team


def _get_team_by_url(url):
    team = {}
    if url and url.startswith('/hub/team/'):
        fields = url.split('/')
        if len(fields) != 5:
            return team
        _, _, _, uid, _ = fields
        team = _get_team_by_uid(uid)
    return team


def _format_commit_object_data(data):
    _project = _get_project_by_name(data.repo_name)
    # _project['branch'] = data.branch if 'branch' in data else ""
    # _project['reference'] = data.ref if 'ref' in data else ""
    _author = dict(
        name=data.author.name,
        email=data.author.email
    )
    commit = dict(
        sha=data.sha,
        author=_author,
        project=_project,
        message=data.message,
        date=data.committer_time.strftime('%Y-%m-%d %H:%M:%S'),
    )
    return commit


def _format_commit_data(data):
    _project = _get_project_by_name(data.get('repo_name'))
    _project['branch'] = data.get('branch') if 'branch' in data else ""
    _project['reference'] = data.get('ref') if 'ref' in data else ""
    _author = dict(
        name=data.get('author').get('name'),
        email=data.get('email')
    )
    commit = dict(
        sha=data.get('commit_id'),
        author=_author,
        project=_project,
        message=data.get('message'),
        date=data.get('timestamp'),
    )
    return commit


def _get_commit_comment_by_uid(uid):
    comment = {}
    if uid and uid.startswith('commit'):
        fields = uid.split('-')
        if len(fields) != 3:
            return comment
        _, comment_type, id = fields
        type = 'line' if comment_type == 'linecomment' else 'comment'
        comment = dict(
            id=id,
            type=type,
        )
    return comment


def _format_repository_data(data):
    _author = _get_user_by_name(data.get('author'))
    _project = _get_project_by_name(data.get('name'))
    if not (_project and _author):
        return {}

    if data['type'] == 'repo_create':
        type = 'create_repo'
    elif data['type'] == 'repo_watch':
        type = 'watch_repo'
    elif data['type'] == 'repo_fork':
        type = 'fork_repo'
        _project['from_project'] = _get_project_by_name(
            data.get('forked_from_name')
        )
    return dict(
        type=type,
        author=_author,
        project=_project,
        content=data['desc'],
        timestamp=data['date'],
    )


def _format_pullrequest_data(data):
    if data['type'] == 'pull_request':
        if data['status'] == 'merged':
            type = 'merge_pr'
            _author = _get_user_by_name(data.get('owner'))
        elif data['status'] == 'unmerge':
            type = 'open_pr'
            _author = _get_user_by_name(data.get('commiter'))
        elif data['status'] == 'closed':
            type = 'close_pr'
            _author = _get_user_by_name(data.get('commiter'))
        else:
            type = 'unkown_pr'
        uid = data.get('uid')
        _pr = _get_pr_by_uid(uid)
        _content = data['description']
        _data = dict(
            type=type,
            author=_author,
            pr=_pr,
            content=_content,
            timestamp=data['date'],
        )
    elif data['type'] == 'code_review':
        type = 'comment_pr'
        _author = _get_user_by_name(data.get('author'))
        uid = data.get('uid')
        _comment = _get_code_review_by_uid(uid)
        _content = data['text']
        _data = dict(
            type=type,
            author=_author,
            comment=_comment,
            content=_content,
            timestamp=data['date'],
        )
    return _data


def _get_issue_by_uid(uid):
    issue = {}
    # uid: issue-type-id-number
    if uid and uid.startswith('issue-'):
        fields = uid.split('-')
        if len(fields) != 4:
            return issue
        _, type, id, number = fields
        if type == 'project':
            _issue = ProjectIssue.get(id, number=number)
            _issue = Issue.get_cached_issue(_issue.issue_id)
            _target = _get_project_by_name(_issue.target.name)
        elif type == 'team':
            _issue = TeamIssue.get(id, number=number)
            _issue = Issue.get_cached_issue(_issue.issue_id)
            _target = _get_team_by_uid(_issue.target.uid)
        else:
            return issue
    _author = _get_user_by_name(_issue.creator_id)
    _closer = _get_user_by_name(_issue.closer_id) if _issue.closer_id else {}
    issue = dict(
        id=_issue.issue_id,
        name=_issue.title,
        author=_author,
        closer=_closer,
    )
    issue[_issue.target_type] = _target
    return issue


def _format_issue_data(data):
    if data['state'] == 'closed':
        type = 'close_issue'
    elif data['state'] == 'open':
        type = 'open_issue'
    _author = _get_user_by_name(data.get('author'))
    _project_name = data.get('proj', None)
    if not _project_name:
        _issue = _get_issue_by_uid(data.get('uid'))
    else:
        _project = _get_project_by_name(_project_name)
        _issue = _get_issue_by_project_and_number(
            _project['id'],
            data.get('number')
        )
        _issue['project'] = _project
    content = data['text']
    return dict(
        type=type,
        author=_author,
        issue=_issue,
        content=content,
        timestamp=data['date'],
    )


def _get_issue_comment_by_uid(uid):
    issue = {}
    # uid: issue-type-id-number
    if uid and uid.startswith('issue-'):
        fields = uid.split('-')
        if len(fields) != 6:
            return issue
        _, _, type, id, number, comment_number = fields
        if type == 'project':
            _issue = ProjectIssue.get(id, number=number)
            _issue = Issue.get_cached_issue(_issue.issue_id)
            _target = _get_project_by_name(_issue.target.name)
        elif type == 'team':
            _issue = TeamIssue.get(id, number=number)
            _issue = Issue.get_cached_issue(_issue.issue_id)
            _target = _get_team_by_uid(_issue.target.uid)
        else:
            return issue
    _author = _get_user_by_name(_issue.creator_id)
    _closer = _get_user_by_name(_issue.closer_id) if _issue.closer_id else {}
    issue = dict(
        id=_issue.issue_id,
        name=_issue.title,
        author=_author,
        closer=_closer,
    )
    issue[_issue.target_type] = _target
    return issue


def _format_issue_comment_data(data):
    type = 'comment_issue'
    _author = _get_user_by_name(data.get('author'))
    _issue = _get_issue_comment_by_uid(data.get('uid'))
    content = data['text']
    return dict(
        type=type,
        author=_author,
        issue=_issue,
        content=content,
        timestamp=data['date'],
    )


def _format_gist_data(data):
    _author = _get_user_by_name(data.get('author'))
    _gist = _get_gist_by_uid(data.get('uid'))
    if data['type'] == 'gist_created':
        type = 'create_gist'
        content = data['desc']
    elif data['type'] == 'gist_commented':
        type = 'comment_gist'
        content = data['content']
    elif data['type'] == 'gist_starred':
        type = 'star_gist'
        content = data['desc']
    elif data['type'] == 'gist_updated':
        type = 'update_gist'
        content = data['desc']
    elif data['type'] == 'gist_forked':
        type = 'fork_gist'
        content = data['desc']
    return dict(
        type=type,
        author=_author,
        gist=_gist,
        content=content,
        timestamp=data['date'],
    )


def _format_people_data(data):
    if data['type'] == 'recommend':
        type = 'recommend_people'
        _author = _get_user_by_name(data.get('sender'))
        _recommend = _get_user_by_name(data.get('to_user'))
        content = data['content']
        _data = dict(
            type=type,
            author=_author,
            recommend=_recommend,
            content=content,
            timestamp=data['date'],
        )
    elif data['type'] == 'commit_comment':
        type = 'comment_commit'
        _author = _get_user_by_name(data.get('sender'))
        _project = _get_project_by_name(data.get('proj'))
        _project['reference'] = data.get('ref')
        _comment = _get_commit_comment_by_uid(data.get('uid'))
        content = data.get('message') or data.get('content')
        _data = dict(
            type=type,
            author=_author,
            project=_project,
            comment=_comment,
            content=content,
            timestamp=data['date'],
        )
    elif data['type'] == 'push':
        type = 'push'
        _project = _get_project_by_name(data.get('repo_name'))
        _project['branch'] = data.get('branch')
        _project['reference'] = data.get('ref')
        commits = data['commits']
        if len(commits) > 3:
            commit = commits[:3]
        else:
            commit = commits
        _commit = [_format_commit_data(c) for c in commit]
        _data = dict(
            type=type,
            project=_project,
            commit=_commit,
            timestamp=data['date']
        )
    return _data


def _format_team_data(data):
    _author = _get_user_by_name(data.get('author'))
    _team = _get_team_by_url(data.get('url'))
    if data['type'] == 'team_created':
        type = 'create_team'
    elif data['type'] == 'team_joined':
        type = 'join_team'
    return dict(
        type=type,
        author=_author,
        team=_team,
        timestamp=data['date'],
    )


def format_timeline(data):
    type = data.get('type')
    if type in ('team_created', 'team_joined'):
        _data = _format_team_data(data)
    elif type in ('recommend', 'commit_comment', 'push'):
        _data = _format_people_data(data)
    elif type in ('gist_created', 'gist_commented',
                  'gist_starred', 'gist_updated',
                  'gist_forked'):
        _data = _format_gist_data(data)
    elif type in ('issue'):
        _data = _format_issue_data(data)
    elif type in ('issue_comment'):
        _data = _format_issue_comment_data(data)
    elif type in ('pull_request', 'code_review'):
        _data = _format_pullrequest_data(data)
    elif type in ('repo_create', 'repo_watch', 'repo_fork'):
        _data = _format_repository_data(data)
    else:
        logging.debug("unknown data type %s." % data.get('type'))
        _data = {}
    return _data
