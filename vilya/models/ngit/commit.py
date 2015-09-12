# -*- coding: utf-8 -*-

from __future__ import absolute_import

from collections import OrderedDict
from datetime import datetime
from pytz import FixedOffset

from vilya.libs.text import email_normalizer
from vilya.libs.text import remove_unknown_character
from vilya.libs.text import render_commit_message
from vilya.models.user import User, get_author_by_email
from vilya.models.utils.decorators import cached_property
from vilya.models.ngit.diff import Diff
from vilya.config import DOMAIN


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
        self.has_author_link = True

        # author
        author_name = commit['author']['name']
        self.author_name = author_name
        author_email = commit['author']['email']
        self.author_email = author_email
        self.email = author_email
        code_author_name = get_author_by_email(author_email, None)
        if code_author_name is None:
            self.has_author_link = False
            author = User(name=author_name, email=author_email)
        else:
            author = User(name=code_author_name, email=author_email)
        self.author = author
        author_date = datetime.fromtimestamp(
            commit['author']['time'],
            FixedOffset(commit['author']['offset']))
        self.author_time = author_date
        author_timestamp = str(commit['author']['time'])
        self.author_timestamp = author_timestamp
        self.time = author_date

        # committer
        committer_name = commit['committer']['name']
        committer_email = email_normalizer(committer_name,
                                           commit['committer']['email'])
        committer = User(name=committer_name, email=committer_email)
        self.committer = committer
        committer_date = datetime.fromtimestamp(
            commit['committer']['time'],
            FixedOffset(commit['committer']['offset']))
        self.committer_time = committer_date
        self.commit_time = committer_date  # FIXME: remove this!

    @property
    def url(self):
        return '/%s/commit/%s/' % (self.repo_name, self.sha)

    @property
    def full_url(self):
        return "%s%s" % (DOMAIN, self.url)

    # FIXME: get Blob instance, then resolve submodule url
    def get_blob_url(self, blob_path):
        return '/%s/blob/%s/%s' % (self.repo_name, self.sha, blob_path)

    def get_url_with_path(self, path):
        """will only show the diff about the path"""
        return '%ssrc/%s' % (self.url, path)

    @property
    def rendered_message(self):
        return render_commit_message(self.message, self.repo.project)

    @property
    def rendered_message_header(self):
        return render_commit_message(self.message_header, self.repo.project)

    @property
    def rendered_message_body(self):
        return render_commit_message(self.message_body, self.repo.project)

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
        raw_diff = repo.get_raw_diff(self.sha)
        diff = Diff(repo, raw_diff) if raw_diff else None
        return diff

    def as_dict(self, with_files=False):
        d = OrderedDict([
            ("id", self.sha),
            ("name", self.author_name),
            ("email", self.author_email),
            ("parents", self.parents),
            ("date", self.committer_time.strftime('%Y-%m-%dT%H:%M:%S+0800')),
            ("message", self.message),
        ])
        if len(self.parents) > 1:
            # Used in PIN
            d['merge'] = ' '.join(sha[:7] for sha in self.parents)
        if with_files:
            files = []
            for delta in self.diff.deltas:
                files.append(dict(type=delta.status_text,
                                  filepath=delta.new_file_path))
            d['files'] = files
        return d
