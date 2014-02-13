# -*- coding: utf-8 -*-

from __future__ import absolute_import

from collections import OrderedDict
from datetime import datetime
from pytz import FixedOffset
from code.libs.text import remove_unknown_character
from code.libs.text import render_commit_message
from code.libs.text import email_normalizer
from code.models.user import User
from code.models.utils.decorators import cached_property
from code.models.git.diff import Diff


class Commit(object):

    def __init__(self, repo, commit):
        self.repo = repo
        self._commit = commit
        self.type = 'commit'
        self.repo_name = repo.name
        parent = commit['parent'][0] if commit['parent'] else None
        self.parent = parent
        self.parents = commit['parent']
        message = ("%s\n\n%s" % (
            commit['message'],
            remove_unknown_character(commit['body']))
        ).strip()
        self.message = message
        self.message_header = commit['message']
        self.message_body = commit['body']
        self.sha = commit['sha']
        self.tree = commit['tree']

        author_name = commit['author']['name']
        self.author_name = author_name
        author_email = email_normalizer(author_name, commit['author']['email'])
        self.author_email = author_email
        self.email = author_email
        # FIXME: user
        #author = User(name=author_name, email=author_email)
        author = User.get_by_name(author_name)
        self.author = author
        author_date = datetime.fromtimestamp(commit['author']['time'],
                                             FixedOffset(commit['author']['offset']))
        author_timestamp = str(commit['author']['time'])
        self.author_time = author_date
        self.author_timestamp = author_timestamp
        self.time = author_date

        committer_name = commit['committer']['name']
        committer_email = email_normalizer(
            committer_name, commit['committer']['email'])
        # FIXME: user
        #committer = User(name=committer_name, email=committer_email)
        committer = User.get_by_name(committer_name)
        self.committer = committer
        committer_date = datetime.fromtimestamp(commit['committer']['time'],
                                             FixedOffset(commit['committer']['offset']))
        self.committer_time = committer_date

    @property
    def url(self):
        return '/%s/commit/%s/' % (self.repo_name, self.sha)

    @property
    def rendered_message(self):
        return render_commit_message(self.message, self.repo.project)

    @property
    def shortlog(self):
        # no commit log...
        if not self.message:
            return ''
        return self.message.splitlines()[0]

    @property
    def shortsha(self):
        return self.sha[:7]

    def has_only_shortlog(self):
        return self.shortlog.strip() == self.message.strip()

    @cached_property
    def diff(self):
        repo = self.repo
        parent = self.parent
        raw_diff = repo.get_raw_diff(self.sha, from_ref=parent)
        diff = Diff(repo, raw_diff) if raw_diff else None
        return diff

    def as_dict(self, with_files=False):
        d = OrderedDict([
            ("id", self.sha),
            ("sha", self.sha),
            ("name", self.author_name),
            ("email", self.author_email),
            ("parents", self.parents),
            ("date", self.committer_time.strftime('%Y-%m-%dT%H:%M:%S+0800')),
            ("message", self.message),
        ])
        if len(self.parents) > 1:
            d['merge'] = ' '.join(sha[:7] for sha in self.parents)  # Used in PIN
        if with_files:
            files = []
            for delta in self.diff.deltas:
                files.append(dict(type=delta.status_text, filepath=delta.new_file_path))
            d['files'] = files
        return d

