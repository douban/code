# -*- coding: utf-8 -*-

import json
from datetime import datetime

from vilya.libs.rdstore import rds
from vilya.libs.signals import (
    pullrequest_signal, codereview_signal, rds_pub_signal,
    push_signal, gist_created_signal, gist_commented_signal,
    gist_starred_signal, gist_updated_signal, gist_forked_signal,
    repo_create_signal, repo_watch_signal, repo_fork_signal,
    team_created_signal, team_joined_signal, issue_signal,
    issue_comment_signal, follow_user_signal)
from vilya.models.utils import (
    CJsonEncoder, format_pullrequest_info, format_code_review_info,
    format_issue_info, format_issue_comment_info, to_timestamp,
    get_issue_by_issue_id)
from vilya.models.notification import (
    get_issue_notify_receivers, get_pr_notify_receivers)
from vilya.models.project import CodeDoubanProject
from vilya.models.team import TeamProjectRelationship
from vilya.models.gist import Gist
from vilya.models.user import User
from vilya.models.pull import PullRequest

MAX_ACTIONS_COUNT = 1009  # Happy Number
RDS_USER_INBOX_KEY = 'feed:private:user:v2:%s'
RDS_USER_FEED_KEY = 'feed:public:user:v2:%s'
RDS_PUBLIC_FEED_KEY = 'feed:public:everyone:v2'
RDS_TEAM_FEED_KEY = 'feed:public:team:v2:%s'
PAGE_ACTIONS_COUNT = 35


class Feed(object):

    def __init__(self, db_key):
        self.db_key = db_key

    def __repr__(self):
        return '%s (%s)' % (self.__class__, self.db_key)

    @classmethod
    def get(cls, db_key):
        return cls(db_key=db_key)

    def add_action(self, action_data):
        data = json.dumps(action_data, cls=CJsonEncoder)
        # the order of args to zadd is reversed in redis-py from that in redis
        print rds, data, self.db_key, action_data
        rds.zadd(self.db_key, data, to_timestamp(action_data.get('date')))
        rds.zremrangebyrank(self.db_key, 0, -1 * (MAX_ACTIONS_COUNT + 1))
        rds_pub_signal.send('feed_add_action',
                            data=data,
                            channel=self.db_key,
                            is_notify=False,
                            show_avatar=True)

    def get_actions(self, start=0, stop=MAX_ACTIONS_COUNT):
        data = rds.zrevrange(self.db_key, start, stop)
        return [json.loads(d) for d in data]

    def get_actions_by_timestamp(self, max='+inf', min='-inf'):
        data = rds.zrevrangebyscore(self.db_key, max, min)
        return [json.loads(d) for d in data]


# new dispatchable feedmsg
class FeedMsg(object):
    def __init__(self, sender, receivers, project=None, data=None,
                 team_id=None):
        # FIXME: args' order
        self._sender = sender
        self._receivers = set(receivers) if receivers else set()
        self._project = project
        self._team_id = team_id
        self._data = data

    def send(self):
        feeds = [self.get_user_feed()]
        feeds += [self.get_public_feed()]
        feeds += self.get_related_user_inbox_feeds()
        feeds += self.get_related_team_feeds()
        for feed in feeds:
            feed.add_action(self._data)

    def get_related_user_inbox_feeds(self):
        ''' user_timeline of actor, actor's followers, project owner,
            project's watchers, extra_receivers '''
        sender = User(self._sender)
        followers = sender.get_followers() if sender else []
        project = self._project
        if project:
            proj_users = [u.username for u in project.get_watch_users()]
            proj_users.append(project.owner.username)
        else:
            proj_users = []
        receivers = {self._sender} | set(followers) | set(proj_users) | self._receivers  # noqa
        return [get_user_inbox(r) for r in receivers]

    def get_related_team_feeds(self):
        ''' team_timeline of project related team, team_ids '''
        project = self._project
        team_id = {self._team_id} if self._team_id else set()
        if project:
            rls = TeamProjectRelationship.gets(project_id=project.id)
            related_team_ids = [rl.team_id for rl in rls]
        else:
            related_team_ids = []
        team_ids = team_id | set(related_team_ids)
        return [get_team_feed(t) for t in team_ids]

    def get_public_feed(self):
        ''' public_timeline '''
        return get_public_feed()

    def get_user_feed(self):
        ''' user_profile_timeline of actor '''
        return get_user_feed(self._sender)


def get_user_inbox(user):
    return Feed.get(db_key=RDS_USER_INBOX_KEY % user)


def get_user_feed(user):
    return Feed.get(db_key=RDS_USER_FEED_KEY % user)


def get_public_feed():
    return Feed.get(db_key=RDS_PUBLIC_FEED_KEY)


def get_team_feed(team):
    return Feed.get(db_key=RDS_TEAM_FEED_KEY % team)


def get_related_feeds(actor, project=None, extra_receivers=[], team_ids=[]):
    # FIXME: team_ids->team_id, 貌似没看到 team_ids 的需求
    ''' user_timeline of actor, actor's followers, project owner,
        project's watchers, extra_receivers;
        team_timeline of project related team, team_ids;
        public_timeline;
        user_profile_timeline of actor '''
    followers = User(actor).get_followers() if actor else []
    proj_users = []
    if project:
        proj_users += [u.username for u in project.get_watch_users()]
        proj_users.append(project.owner.username)
    users = filter(None, list(set(
        [actor] + followers + proj_users + list(extra_receivers))))
    feeds = [get_user_inbox(user) for user in users]
    if project:
        rls = TeamProjectRelationship.gets(project_id=project.id)
        feeds.extend([get_team_feed(rl.team_id) for rl in rls])
    if team_ids:
        feeds.extend([get_team_feed(id) for id in team_ids])
    feeds.append(get_public_feed())
    if actor:
        feeds.append(get_user_feed(actor))
    return feeds


@codereview_signal.connect
def add_code_review_action(sender, **kw):
    data = format_code_review_info(sender, **kw)
    ticket = kw['ticket']
    author = kw['author']
    pullreq = PullRequest.get_by_ticket(ticket)
    feeds = get_related_feeds(author, pullreq.to_proj)
    for feed in feeds:
        feed.add_action(data)


@pullrequest_signal.connect
def add_pullrequest(sender, **kw):
    extra_receivers = kw.get('extra_receivers', [])
    pullreq = kw.get('pullreq')
    comment = kw.get('comment')
    ticket = kw.get('ticket')

    to_users = get_pr_notify_receivers(sender, comment, pullreq, ticket,
                                       extra_receivers=extra_receivers)

    data = format_pullrequest_info(sender, **kw)
    feeds = get_related_feeds(data.get('commiter'), pullreq.to_proj, to_users)
    for feed in feeds:
        feed.add_action(data)


@team_created_signal.connect
def team_created_data(sender, **kw):
    date = datetime.now()
    team_uid = kw.get('team_uid', '')
    team_name = kw.get('team_name', '')
    data = {
        'author': sender,
        'type': 'team_created',
        'url': '/hub/team/%s/' % team_uid,
        'name': team_name,
        'date': date
    }
    feeds = get_related_feeds(sender)
    for feed in feeds:
        feed.add_action(data)


@team_joined_signal.connect
def team_joined_data(sender, **kw):
    date = datetime.now()
    team_uid = kw.get('team_uid')
    team_id = kw.get('team_id')
    data = {
        'author': sender,
        'type': 'team_joined',
        'url': '/hub/team/%s/' % team_uid,
        'name': kw.get('team_name', ''),
        'date': date
    }
    feeds = get_related_feeds(sender, team_ids=[team_id, ])
    for feed in feeds:
        feed.add_action(data)


@push_signal.connect
def push_data_receiver(sender, **kw):
    EMPTY_COMMIT_HASH = "0" * 40
    date = datetime.now()
    repo_name = kw.get('repo_name')
    before = kw.get('before')
    after = kw.get('after')
    username = kw.get('username')
    data = {
        'repo_name': repo_name,
        'repo_url': kw.get('repo_url'),
        'ref': kw.get('ref'),
        'branch': kw.get('branch'),
        'date': date,
        'before': before,
        'after': after,
        'is_new_branch': before == EMPTY_COMMIT_HASH,
        'is_delete_branch': after == EMPTY_COMMIT_HASH,
        'commits': kw.get('commits'),
        'type': 'push',
        'username': username,
    }
    feeds = get_related_feeds(
        '', project=CodeDoubanProject.get_by_name(repo_name))
    for feed in feeds:
        feed.add_action(data)


@gist_created_signal.connect
def gist_created_receiver(sender, **kw):
    gist_id = kw.get('gist_id')
    gist = Gist.get(gist_id)
    data = {
        'uid': 'gist-create-%s' % gist.id,
        'author': gist.owner_id,
        'url': gist.url,
        'name': gist.name,
        'desc': gist.description,
        'date': gist.created_at,
        'type': 'gist_created',
    }
    feeds = get_related_feeds(gist.owner_id)
    for feed in feeds:
        feed.add_action(data)


@gist_commented_signal.connect
def gist_commented_receiver(sender, **kw):
    gist_id = kw.get('gist_id')
    gist = Gist.get(gist_id)
    comment = kw.get('comment')
    data = {
        'uid': 'gist-comment-%s' % gist.id,
        'author': comment.user_id,
        'name': gist.full_name,
        'url': comment.url,
        'content': comment.content,
        'date': comment.created_at,
        'type': 'gist_commented',
    }
    feeds = get_related_feeds('', extra_receivers=[gist.owner_id])
    for feed in feeds:
        feed.add_action(data)


@gist_starred_signal.connect
def gist_starred_receiver(sender, **kw):
    author = kw.get('author')
    gist_id = kw.get('gist_id')
    gist = Gist.get(gist_id)
    uid = 'gist-star-%s-%s' % (gist.id, author)
    data = {
        'uid': uid,
        'author': author,
        'url': gist.url,
        'name': gist.full_name,
        'desc': gist.description,
        'date': datetime.now(),
        'type': 'gist_starred'
    }
    feeds = get_related_feeds(author, extra_receivers=[gist.owner_id])
    for feed in feeds:
        feed.add_action(data)


@gist_forked_signal.connect
def gist_forked_receiver(sender, **kw):
    gist_id = kw.get('gist_id')
    gist = Gist.get(gist_id)
    forked_from = gist.forked_from
    uid = 'gist-fork-%s-%s' % (forked_from.id, gist.id)
    data = {
        'uid': uid,
        'author': gist.owner_id,
        'forked_from_name': forked_from.full_name,
        'forked_from_url': forked_from.url,
        'url': gist.url,
        'name': gist.full_name,
        'desc': gist.description,
        'date': gist.created_at,
        'type': 'gist_forked'
    }
    feeds = get_related_feeds(
        gist.owner_id, extra_receivers=[forked_from.owner_id])
    for feed in feeds:
        feed.add_action(data)


@gist_updated_signal.connect
def gist_updated_receiver(sender, **kw):
    gist_id = kw.get('gist_id')
    gist = Gist.get(gist_id)
    data = {
        'uid': 'gist-update-%s' % gist.id,
        'author': gist.owner_id,
        'url': gist.url,
        'name': gist.full_name,
        'desc': gist.description,
        'date': gist.updated_at,
        'type': 'gist_updated'
    }
    feeds = get_related_feeds(gist.owner_id)
    for feed in feeds:
        feed.add_action(data)


@repo_create_signal.connect
def repo_create_receiver(sender, **kw):
    proj_id = kw.get('project_id')
    owner_id = kw.get('creator')
    project = CodeDoubanProject.get(proj_id)
    uid = 'repo-create-%s-%s' % (project.id, owner_id)
    data = {
        'uid': uid,
        'author': owner_id,
        'url': project.url,
        'name': project.name,
        'desc': project.summary,
        'date': datetime.now(),
        'type': 'repo_create'
    }
    feeds = get_related_feeds(owner_id)
    for feed in feeds:
        feed.add_action(data)


@repo_watch_signal.connect
def repo_watch_receiver(sender, **kw):
    proj_id = kw.get('project_id')
    author = kw.get('author')
    project = CodeDoubanProject.get(proj_id)
    uid = 'repo-watch-%s-%s' % (project.id, author)
    data = {
        'uid': uid,
        'author': author,
        'url': project.url,
        'name': project.name,
        'desc': project.summary,
        'date': datetime.now(),
        'type': 'repo_watch'
    }
    feeds = get_related_feeds(author)
    for feed in feeds:
        feed.add_action(data)


@repo_fork_signal.connect
def repo_fork_receiver(sender, **kw):
    proj_id = kw.get('project_id')
    author = kw.get('author')
    project = CodeDoubanProject.get(proj_id)
    forked_from = project.get_forked_from()
    uid = 'repo-fork-%s-%s' % (forked_from.id, project.id)
    data = {
        'uid': uid,
        'author': author,
        'forked_from_name': forked_from.name,
        'forked_from_url': forked_from.url,
        'url': project.url,
        'name': project.name,
        'desc': project.summary,
        'date': datetime.now(),
        'type': 'repo_fork'
    }
    feeds = get_related_feeds(author, extra_receivers=[forked_from.owner_id])
    for feed in feeds:
        feed.add_action(data)


@issue_signal.connect
def add_issue_action(sender, **kw):
    author = kw['author']
    content = kw['content']
    issue_id = kw['issue_id']

    data = format_issue_info(**kw)
    issue = get_issue_by_issue_id(issue_id)
    target = issue.target

    to_users = get_issue_notify_receivers(author, content, target, issue)
    if issue.target_type == "project":
        feeds = get_related_feeds(
            author, project=target, extra_receivers=to_users)
    elif issue.target_type == "team":
        feeds = get_related_feeds(
            author, extra_receivers=to_users, team_ids=[target.id])
    elif issue.target_type == "fair":
        from vilya.models.fair import FAIR_ID
        feeds = get_related_feeds(author, extra_receivers=to_users,
                                  team_ids=[FAIR_ID])
    for feed in feeds:
        feed.add_action(data)


@issue_comment_signal.connect
def add_issue_comment_action(sender, **kw):
    author = kw['author']
    content = kw['content']
    issue_id = kw['issue_id']

    issue = get_issue_by_issue_id(issue_id)
    target = issue.target

    data = format_issue_comment_info(**kw)
    to_users = get_issue_notify_receivers(author, content, target, issue)
    if issue.target_type == "project":
        feeds = get_related_feeds(
            author, project=target, extra_receivers=to_users)
    elif issue.target_type == "team":
        feeds = get_related_feeds(
            author, extra_receivers=to_users, team_ids=[target.id])
    elif issue.target_type == "fair":
        from vilya.models.fair import FAIR_ID
        feeds = get_related_feeds(author, extra_receivers=to_users,
                                  team_ids=[FAIR_ID])
    for feed in feeds:
        feed.add_action(data)


@follow_user_signal.connect
def follow_user_action(sender, **kw):
    author = kw['author']
    followee = kw['followee']
    data = {
        "author": author,
        "followee": followee,
        'date': datetime.now(),
        'type': 'follow_user'
    }

    feeds = get_related_feeds(author, extra_receivers=[followee])
    for feed in feeds:
        feed.add_action(data)
