# -*- coding: utf-8 -*-

from __future__ import absolute_import

import os
from datetime import datetime
from urllib import urlencode

from quixote import get_user as get_current_user_id, get_session

from vilya.libs.store import store, cache, mc, ONE_MONTH
from vilya.libs.text import gravatar_url
from vilya.libs.props import PropsMixin, PropsItem
from vilya.libs.validators import check_email, check_name
from vilya.libs.signals import follow_user_signal

from vilya.models.inbox import Inbox
from vilya.models.badge import Badge
from vilya.models.user_issue import UserIssue
from vilya.models.project_issue import ProjectIssue
from vilya.models.consts import (
    NOTIFY_ON, SETTING_DISABLE, FONTS)
from vilya.models.sshkey import SSHKey
from vilya.models.utils import check_douban_email
from vilya.models.nuser import User2 as CodeUser


def set_user(user_id):
    session = get_session()
    session.set_user(user_id)


def _get_full_qualified_url(url):
    # from urlparse import urljoin
    # env = get_environ()
    # env['PATH_INFO'] = ''
    # req = Request(env)
    # urljoin(req.url, url)
    return url


def get_current_user():
    """Returns the L{User} object for the current user (the user who made the
    request being processed) if the user is signed in, or None if the user is
    not signed in.
    """
    id = get_current_user_id()
    user = CodeUser.get(id=id)
    return User(user.name) if user else None


class User(PropsMixin):

    trello_access_token = PropsItem('trello_access_token')
    trello_request_token = PropsItem('trello_request_token')

    def __init__(self, name, email=None, dae_user=None):
        name = str(name) if not isinstance(name, unicode) \
            else name.encode('utf-8')
        self.name = name
        self.dae_user = dae_user
        self.username = self.name
        self._email = email
        self._code_user = None

    def __str__(self):
        return self.name

    def __eq__(self, y):
        return y and isinstance(y, User) and \
            self.name == y.name and self.email == y.email

    @classmethod
    def check_exist(cls, name):
        return bool(cls.get_by_name(name))

    @classmethod
    def get_by_name(cls, name):
        return CodeUser.get(name=name)

    @classmethod
    def create_register_url(cls, dest_url=None, full_url=False):
        return cls.create_url('/register/', dest_url=dest_url,
                              full_url=full_url)

    @classmethod
    def create_login_url(cls, dest_url=None, full_url=False):
        return cls.create_url('/login/', dest_url=dest_url, full_url=full_url)

    @classmethod
    def create_logout_url(cls, dest_url, full_url=False):
        return cls.create_url('/logout/', dest_url=dest_url, full_url=full_url)

    @classmethod
    def create_url(cls, url, dest_url=None, full_url=False):
        if dest_url:
            url += '?' + urlencode({'continue': dest_url})
        return _get_full_qualified_url(url) if full_url else url

    @property
    def teams(self):
        from vilya.models.nteam import TeamUserRelationship
        from vilya.models.team import Team

        rs = TeamUserRelationship.gets(user_id=self.name)
        return filter(None, [Team.get(r.team_id) for r in rs])

    @property
    def code_user(self):
        if not self._code_user:
            self._code_user = CodeUser.get(name=self.username)
        return self._code_user

    @property
    def profile(self):
        return {'email': self.username}

    @classmethod
    def get_current_user(cls):
        user = get_current_user()
        if not user:
            return
        return cls(user.username, user.profile.get('email'), user)

    # FIXME: User或许应该加个id属性
    def get_uuid(self):
        return '/user/%s' % self.username

    @property
    def url(self):
        return '/people/%s/' % self.username

    # NOTE: 现在通过 add_codeuser_role 判断 intern
    @property
    def is_intern(self):
        if self.username.endswith('_intern'):
            return True
        code_user = self.code_user
        if code_user and code_user.is_intern:
            return True
        return False

    @property
    def avatar_url(self):
        return gravatar_url(self.email)

    def avatar_in_size(self, size):
        return gravatar_url(self.email, size)

    def has_id(self):
        return bool(self.code_user)

    def has_role(self):
        code_user = self.code_user
        return code_user.has_role() if code_user else None

    @property
    def inbox(self):
        return Inbox.get(user=self.name)

    @property
    def unread_notification_count(self):
        from vilya.models.notification import Notification
        return Notification.unread_count(self.name)

    @property
    def settings(self):
        return UserSettings(self.username)

    @property
    def email(self):
        if not self._email:
            if self.is_intern:
                if self.username.endswith('_intern'):
                    self._email = self.username + '@douban.com'
                else:
                    self._email = self.username + '@intern.douban.com'
            else:
                self._email = self.username + '@douban.com'
        return self._email

    def as_dict(self):
        d = {}
        d['name'] = self.username
        d['email'] = self.email
        d['url'] = self.url
        d['is_intern'] = self.is_intern
        d['avatar_url'] = self.avatar_url
        d['badges'] = [item.as_dic() for item in self.get_badge_items()]
        d['followers_count'] = self.followers_count
        d['following_count'] = self.following_count
        return d

    @classmethod
    def get_by_email(cls, email):
        username = None
        if check_douban_email(email):
            username = email.split('@')[0]
        else:
            user_email = CodeDoubanUserEmails.get_by_email(email)
            username = user_email.user_id if user_email else None
        return cls(username) if username else None

    def get_badges(self):
        return Badge.get_badges(self.username)

    def get_badge_items(self):
        return Badge.get_badge_items(self.username)

    def get_new_badges(self):
        return Badge.get_new_badges(self.username)

    def clear_new_badges(self):
        return Badge.clear_new_badges(self.username)

    def get_followers(self):
        return FollowRelationship.get_followers(self.username)

    @property
    def followers_count(self):
        return FollowRelationship.get_followers_count(self.username)

    def is_following(self, username):
        return FollowRelationship.check_exist(username, self.username)

    def get_following(self):
        return FollowRelationship.get_following(self.username)

    @property
    def following_count(self):
        return FollowRelationship.get_following_count(self.username)

    def follow(self, username):
        if not FollowRelationship.check_exist(username, self.username):
            FollowRelationship.add(username, self.username)
            follow_user_signal.send(author=self.username, followee=username)

    def unfollow(self, username):
        if FollowRelationship.check_exist(username, self.username):
            FollowRelationship.delete(username, self.username)

    def get_praises(self):
        from vilya.models.recommendation import Recommendation
        return Recommendation.gets_by_user(self.username)

    def add_invited_pull_request(self, ticket_id):
        return UserPullRequests(self.username).add_invited(ticket_id)

    def add_participated_pull_request(self, ticket_id):
        return UserPullRequests(self.username).add_participated(ticket_id)

    def get_invited_pull_requests(self, is_closed=False):
        from vilya.models.ticket import Ticket
        return [Ticket.get(ticket_id)
                for ticket_id in UserPullRequests(
            self.username).get_invited(is_closed)]

    def get_participated_pull_requests(self, is_closed=False):
        from vilya.models.ticket import Ticket
        return [Ticket.get(ticket_id)
                for ticket_id in UserPullRequests(
            self.username).get_participated(is_closed)]

    def get_participated_issues(self, state='open', limit=25, start=0):
        issues = UserIssue.get_participated_issues(self.username, state)
        issues.sort(key=lambda x: x.updated_at, reverse=True)
        return issues[start:start + limit]

    def get_n_participated_issues(self, state='open'):
        issues = UserIssue.get_participated_issues(self.username, state)
        return len(issues)

    def get_user_submit_pull_requests(self, limit=25, is_closed=False):
        from vilya.models.ticket import Ticket
        tickets = Ticket.gets_by_author(
            self.username, limit=limit, closed=is_closed)
        return tickets

    def get_user_pull_requests_rank(self, limit=5):
        from vilya.models.ticket import Ticket
        tickets = Ticket.gets_ranks_by_author(self.username, limit=limit)
        return tickets

    @property
    def n_user_open_submit_pull_requests(self):
        return len(self.get_user_submit_pull_requests())

    @property
    def n_open_invited(self):
        return UserPullRequests(self.username).n_open_invited

    @property
    def n_open_participated(self):
        return UserPullRequests(self.username).n_open_participated

    @property
    def n_open_pull_requests(self):
        return UserPullRequests(self.username).n_open_pull_requests

    @property
    def emails(self):
        ''' return user's other emails '''
        rs = store.execute('select id, email from codedouban_useremails '
                           'where user_id=%s', (self.name,))
        user_emails = [CodeDoubanUserEmails(
            id, self.name, email) for id, email in rs]
        # hack old data
        user_emails = [user_email for user_email in user_emails
                       if user_email.email != self.email]
        return user_emails

    @property
    def githubs(self):
        rs = store.execute('select id, user_name from codedouban_usergithub '
                           'where user_id=%s', (self.name,))
        githubs = [CodeDoubanUserGithub(
            id, self.name, user_name) for id, user_name in rs]
        return githubs

    @property
    def sshkeys(self):
        return SSHKey.gets_by_user_id(self.name)

    def get_n_assigned_issues_by_project(self, project_id, state="open"):
        return ProjectIssue.get_count_by_assignee_id(
            project_id, self.name, state)

    def get_n_created_issues_by_project(self, project_id, state="open"):
        return ProjectIssue.get_count_by_creator_id(
            project_id, self.name, state)

    def get_repos_issues(self, state):
        return UserIssue.gets_by_creator_id(self.name, state)

    def get_created_issues(self, state, limit=25, start=0):
        issues = UserIssue.gets_by_creator_id(self.name, state)
        issues.sort(key=lambda x: x.updated_at, reverse=True)
        return issues[start:start + limit]

    def get_count_created_issues(self, state):
        return len(UserIssue.gets_by_creator_id(self.name, state))

    def get_assigned_issues(self, state, limit=25, start=0):
        issues = UserIssue.gets_by_assignee_id(self.name, state)
        issues.sort(key=lambda x: x.updated_at, reverse=True)
        return issues[start:start + limit]

    def get_count_assigned_issues(self, state):
        return len(UserIssue.gets_by_assignee_id(self.name, state))

    def notify_email(self, target_obj):
        target_type = target_obj.__class__.__name__
        if target_type == "CodeDoubanProject":
            from vilya.models.project import CodeDoubanProject
            if CodeDoubanProject.has_watched(target_obj.id, self) \
               and self.settings.watching_email == NOTIFY_ON:
                return True
            else:
                return self.settings.participating_email == NOTIFY_ON
        elif target_type == "Team":
            return self.settings.participating_email == NOTIFY_ON

    def notify_irc(self, target_obj):
        target_type = target_obj.__class__.__name__
        if target_type == "CodeDoubanProject":
            from vilya.models.project import CodeDoubanProject
            if CodeDoubanProject.has_watched(target_obj.id, self) \
               and self.settings.watching_irc == NOTIFY_ON:
                return True
            else:
                return self.settings.participating_irc == NOTIFY_ON
        elif target_type == "Team":
            return self.settings.participating_irc == NOTIFY_ON

    @property
    def watched_projects(self):
        from vilya.models.project import CodeDoubanProject

        return CodeDoubanProject.get_watched_projects_by_user(
            user=self.username)


class FollowRelationship(object):

    def __init__(self, name, followed_user_name):
        self.name = name
        self.followed_user_name = followed_user_name

    @staticmethod
    def get_followers(name):
        rs = store.execute('select followed_user_name '
                           'from follow_relationship '
                           'where user_name=%s', (name,))
        return [_name for _name, in rs]

    @staticmethod
    def get_followers_count(name):
        rs = store.execute('select count(1) '
                           'from follow_relationship '
                           'where user_name=%s', (name,))
        return rs[0][0]

    @staticmethod
    def get_following(name):
        rs = store.execute('select user_name '
                           'from follow_relationship '
                           'where followed_user_name=%s', (name,))
        return [_name for _name, in rs]

    @staticmethod
    def get_following_count(name):
        rs = store.execute('select count(1) '
                           'from follow_relationship '
                           'where followed_user_name=%s', (name,))
        return rs[0][0]

    @classmethod
    def check_exist(cls, name, followed_user_name):
        rs = store.execute('select count(1) '
                           'from follow_relationship '
                           'where user_name=%s and followed_user_name=%s',
                           (name, followed_user_name))
        if rs:
            return rs[0][0] == 1

    @classmethod
    def add(cls, name, followed_user_name):
        time = datetime.now()
        store.execute('insert into follow_relationship '
                      '(user_name, followed_user_name, time) '
                      'values (%s, %s, %s)',
                      (name, followed_user_name, time))
        store.commit()

    @classmethod
    def delete(cls, name, followed_user_name):
        store.execute('delete from follow_relationship '
                      'where user_name=%s and followed_user_name=%s',
                      (name, followed_user_name))
        store.commit()


class CodeDoubanUserEmails(object):

    def __init__(self, id, user_id, email):
        self.id = int(id)
        self.user_id = user_id
        self.email = email

    @classmethod
    def validate(cls, user_id, email):

        def check_exist(email):
            rs = store.execute(
                'select id from codedouban_useremails where email=%s',
                (email,))
            email_id = rs and rs[0]
            if email_id:
                return 'Email %s is already in use' % email

        def check_default(email):
            if User(name=user_id).email == email:
                return 'Email %s is default' % email

        validators = [check_exist(email), check_email(
            email, 'Email'), check_default(email)]
        errors = [error for error in validators if error]
        return errors

    @classmethod
    def add(cls, user_id, email):
        email_id = store.execute(
            'insert into codedouban_useremails (user_id, email) '
            'values (%s, %s)', (user_id, email))
        store.commit()
        ret = cls(email_id, user_id, email)
        ret._flush()
        return ret

    def delete(self):
        store.execute(
            "delete from codedouban_useremails where id=%s", (self.id,))
        store.commit()
        self._flush()
        return self

    @classmethod
    @cache('email:{email}:user', expire=ONE_MONTH)
    def get_by_email(cls, email):
        rs = store.execute(
            'select id, user_id, email from codedouban_useremails '
            'where email=%s', (email,))
        r = rs and rs[0]
        if rs:
            return cls(*r)

    @classmethod
    def check_own_by_user(cls, user_id, email_id):
        rs = store.execute("select id, user_id, email "
                           "from codedouban_useremails "
                           "where user_id=%s and id=%s",
                           (user_id, email_id))
        r = rs and rs[0]
        if r:
            return cls(*r)

    def _flush(self):
        mc.delete('email:%s:user' % self.email)


class UserSettings(PropsMixin):

    DEFAULT_VALUE = {
        'participating_email': NOTIFY_ON,
        'participating_irc': NOTIFY_ON,
        'participating_web': NOTIFY_ON,
        'watching_email': NOTIFY_ON,
        'watching_irc': NOTIFY_ON,
        'watching_web': NOTIFY_ON,
        'dblclick_comment': SETTING_DISABLE,
        'text_font': FONTS['default'],
        'notif_other_emails': [],
    }

    def __init__(self, user_id):
        self.user_id = user_id

    def get_uuid(self):
        return '/user_settings/%s' % self.user_id

    def __getattr__(self, name):
        if "props" not in name and \
           name not in ['get_uuid', 'props', 'user_id']:
            attr_value = self.get_props_item("/%s" % name)
            if name in self.DEFAULT_VALUE and attr_value is None:
                return self.DEFAULT_VALUE[name]
            return attr_value
        return super(UserSettings, self).__getattr__(name)

    def __setattr__(self, name, value):
        if "props" not in name and \
           name not in ['get_uuid', 'props', 'user_id']:
            self.set_props_item("/%s" % name, value)
        return super(UserSettings, self).__setattr__(name, value)


class UserPullRequests(PropsMixin):
    KEY_INVITED_PRS = "prs/i/u_%s"
    KEY_PATICIPATED_PRS = "prs/p/u_%s"

    def __init__(self, user_id):
        self.user_id = user_id

    def get_uuid(self):
        return '/user_pull_requests/%s' % self.user_id

    @property
    def n_open_invited(self):
        return len(self.get_invited())

    @property
    def n_open_participated(self):
        return len(self.get_participated())

    @property
    def n_open_pull_requests(self):
        return len(set(self.get_invited() + self.get_participated()))

    def _clean_closed_tickets(self):
        from vilya.models.ticket import Ticket
        # FIXME should be async function
        tickets = set(self.get_invited() + self.get_participated())
        for ticket_id in tickets:
            t = Ticket.get(ticket_id)
            if t and t.project and not t.closed:
                continue
            self.remove_invited(ticket_id)
            self.remove_participated(ticket_id)

    def get_invited(self, is_closed=False):
        return self.props.get(self.KEY_INVITED_PRS % self.user_id) or []

    def add_invited(self, ticket_id):
        invited_prs = self.get_invited()
        if ticket_id and ticket_id not in invited_prs:
            invited_prs.append(ticket_id)
            self.set_props_item(
                self.KEY_INVITED_PRS % self.user_id, invited_prs)
        self._clean_closed_tickets()
        return self.get_invited

    def remove_invited(self, ticket_id):
        # FIXME unittest needed, better interface/name to call from outside
        invited_prs = self.get_invited()
        if ticket_id and ticket_id in invited_prs:
            invited_prs.remove(ticket_id)
            self.set_props_item(
                self.KEY_INVITED_PRS % self.user_id, invited_prs)
        return self.get_invited()

    def get_participated(self, is_closed=False):
        return self.props.get(self.KEY_PATICIPATED_PRS % self.user_id) or []

    def add_participated(self, ticket_id):
        participated_prs = self.get_participated()
        if ticket_id and ticket_id not in participated_prs:
            participated_prs.append(ticket_id)
            self.set_props_item(
                self.KEY_PATICIPATED_PRS % self.user_id, participated_prs)
        self._clean_closed_tickets()
        return self.get_participated

    def remove_participated(self, ticket_id):
        # FIXME unittest needed, better interface/name to call from outside
        participated_prs = self.get_participated()
        if ticket_id and ticket_id in participated_prs:
            participated_prs.remove(ticket_id)
            self.set_props_item(
                self.KEY_PATICIPATED_PRS % self.user_id, participated_prs)
        return self.get_participated()


class CodeDoubanUserGithub(object):

    def __init__(self, id, user_id, user_name):
        self.id = int(id)
        self.user_id = user_id
        self.user_name = user_name

    @classmethod
    def validate(cls, user_id, user_name):

        def check_exist(user_name):
            rs = store.execute(
                'select id from codedouban_usergithub where user_name=%s', (user_name,))
            github_id = rs and rs[0]
            if github_id:
                return 'Github user %s is already in use' % user_name

        validators = [check_exist(user_name), check_name(
            user_name, 'Github user name')]
        errors = [error for error in validators if error]
        return errors

    @classmethod
    def add(cls, user_id, user_name):
        github_id = store.execute(
            'insert into codedouban_usergithub (user_id, user_name) values (%s, %s)',
            (user_id, user_name))
        store.commit()
        return cls(github_id, user_id, user_name)

    def delete(self):
        store.execute(
            "delete from codedouban_usergithub where id=%s", (self.id,))
        store.commit()
        return self

    @classmethod
    @cache('github:{user_name}:user', expire=ONE_MONTH)
    def get_by_user_name(cls, user_name):
        rs = store.execute(
            'select id, user_id, user_name from codedouban_usergithub where user_name=%s', (user_name,))
        r = rs and rs[0]
        if rs:
            return cls(*r)

    @classmethod
    def check_own_by_user(cls, user_id, github_id):
        rs = store.execute("select id, user_id, user_name "
                           "from codedouban_usergithub "
                           "where user_id=%s and id=%s",
                           (user_id, github_id))
        r = rs and rs[0]
        if r:
            return cls(*r)


def get_author_by_email(email, author=''):
    # company
    email = email.rstrip('>') if email.endswith('>') else email
    if check_douban_email(email):
        username = email.split('@')[0]
        return username
    user = User.get_by_email(email)
    if check_douban_email(author):
        author = author.split('@')[0]
    return user and user.name or author


def add_codeuser(user):
    CodeUser.add(user.username)


def add_codeuser_role(user):
    if os.environ['DAE_ENV'] == 'SDK':
        return None
    dae_user = user.dae_user
    if not dae_user:
        return None
    email = dae_user.profile.get('email')
    if not email:
        return None
    code_user = CodeUser.get(name=user.username)
    if email.endswith('@douban.com'):
        code_user.set_role()
    elif email.endswith('@intra.douban.com'):
        code_user.set_role(intern=True)


def clean_user_pulls(user):
    if isinstance(user, CodeUser):
        UserPullRequests(user.name)._clean_closed_tickets()


def get_users():
    rs = store.execute('select id from users')
    users = (CodeUser.get(id=id) for id, in rs)
    return users


def judge_user(name):
    from vilya.models.team import Team
    if CodeUser.get(name=name):
        return "people"
    else:
        if Team.get_by_uid(name):
            return "team"
        else:
            return "people"
