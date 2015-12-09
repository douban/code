#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib
import urllib2
import json
from dateutil import parser
from vilya.libs.signals import push_signal
from vilya.models.project import CodeDoubanProject
from vilya.models.user import get_author_by_email
from vilya.models.lru_counter import (ProjectOwnLRUCounter,
                                      ProjectWatchLRUCounter)
from vilya.views.uis.pull import TicketUI


def __enter__(data):
    return data


def async_push_notif(args):
    data = args
    repo = data.get('repository', {})
    repo_name = repo.get('name', '')
    repo_url = repo.get('url', '')
    ref = data.get('ref', '')
    pushername = data.get('user_name')
    branch = ref.split('/')[-1]
    commits = data.get('commits', [])
    commits_data = []
    proj = CodeDoubanProject.get_by_name(repo_name)
    for c in commits:
        author = c.get('author', {})
        email = author.get('email')
        username = get_author_by_email(email)
        if not username:
            continue
        commit_id = c.get('id')
        message = c.get('message')
        timestamp = c.get('timestamp')
        url = '%s/commit/%s' % (repo_url, commit_id)
        ProjectOwnLRUCounter(username).use(proj.id)
        ProjectWatchLRUCounter(username).use(proj.id)
        commits_data.append(dict(repo_name=repo_name,
                                 repo_url=repo_url,
                                 ref=ref,
                                 branch=branch,
                                 author=author,
                                 username=username,
                                 email=email,
                                 commit_id=commit_id,
                                 message=message,
                                 timestamp=parser.parse(timestamp[:-5]),
                                 url=url))

    before = data.get('before')
    after = data.get('after')
    push_signal.send('push',
                     repo_name=repo_name,
                     repo_url=repo_url,
                     ref=ref,
                     branch=branch,
                     commits=commits_data,
                     before=before,
                     after=after,
                     username=pushername)


def async_push_commits(args):
    data = args
    repo = data.get('repository', {})
    repo_name = repo.get('name', '')
    proj = CodeDoubanProject.get_by_name(repo_name)

    # 追加commit到pr
    # FIXME: more project eg: fork network
    opened_pr = proj.open_parent_pulls
    parent_proj = proj.get_forked_from()
    for pr in opened_pr:
        # FIXME: split this or use async
        TicketUI(parent_proj.name, pr.ticket_id)._add_additional_commits()


def async_push_hooks(args):
    data = args
    repo = data.get('repository', {})
    repo_name = repo.get('name', '')
    proj = CodeDoubanProject.get_by_name(repo_name)
    data = json.dumps(data)
    # FIXME: use services
    if proj:
        for h in proj.hooks:
            try:
                u = urllib2.urlopen(h.url, urllib.urlencode({'payload': data}))
                u.read()
                u.close()
            except urllib2.URLError, x:
                print "%s => %s" % (h.url, x)
