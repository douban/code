# -*- coding: utf-8 -*-

from vilya.config import DOMAIN as CODE_URL


class Activity(object):

    def __init__(self, data):
        self.data = data

    def to_line(self):
        return format_activity(self.data)


def format_activity(data):
    type = data.get('type')
    if type in ('team_created', 'team_joined'):
        _data = _format_team_data(data)
    elif type in ('recommend', 'commit_comment', 'push'):
        _data = _format_people_data(data)
    elif type in ('issue'):
        _data = _format_issue_data(data)
    elif type in ('issue_comment'):
        _data = _format_issue_comment_data(data)
    elif type in ('pull_request', 'code_review'):
        _data = _format_pullrequest_data(data)
    return _data


def _format_repository_data(data):
    return ''


def _format_team_data(data):
    _author = data.get('author')
    _team = data.get('name')
    if data['type'] == 'team_created':
        type = 'created'
    elif data['type'] == 'team_joined':
        type = 'joined'
    return "%s %s team:<a href=\"%s\">%s</a>" % (
        _author, type, CODE_URL + data.get('url'), _team)


def _format_issue_data(data):
    if data['state'] == 'closed':
        type = 'closed'
    elif data['state'] == 'open':
        type = 'opened'
    _author = data.get('author')
    tmpl = "%s %s issue:<a href=\"%s\">%s</a> on <a href=\"%s\">%s</a>"
    return tmpl % (_author, type, CODE_URL + data.get('url'),
                   data.get('title'), CODE_URL + data.get('target_url'),
                   data.get('target_name'))


def _format_issue_comment_data(data):
    _author = data.get('author')
    tmpl = "%s commented issue:<a href=\"%s\">%s</a> on <a href=\"%s\">%s</a>"
    return tmpl % (_author, CODE_URL + data.get('url'), data.get('title'),
                   CODE_URL + data.get('target_url'), data.get('target_name'))


def _format_pullrequest_data(data):
    if data['type'] == 'pull_request':
        if data['status'] == 'merged':
            type = 'merged'
            _author = data.get('owner')
        elif data['status'] == 'unmerge':
            type = 'opened'
            _author = data.get('commiter')
        elif data['status'] == 'closed':
            type = 'closed'
            _author = data.get('commiter')
        else:
            type = '?'
            _author = '?'
        _title = data.get('title')
        _url = data.get('url')
        _project = data.get('to_proj', '')
    elif data['type'] == 'code_review':
        type = 'commented'
        _author = data.get('author')
        _title = data.get('ticket')
        _url = data.get('url')
        _project = data.get('proj', '')
    _project_url = "/%s" % _project.split(':')[0]
    tmpl = "%s %s pr:<a href=\"%s\">%s</a> on <a href=\"%s\">%s</a>"
    return tmpl % (_author, type, CODE_URL + _url, _title,
                   CODE_URL + _project_url, _project)


def _format_people_data(data):
    if data['type'] == 'recommend':
        return ''
    elif data['type'] == 'commit_comment':
        type = 'commented'
        _author = data.get('sender')
        _project = data.get('proj')
        _project_url = "/%s" % _project
        return "%s %s <a href=\"%s\">%s</a> on <a href=\"%s\">%s</a>" % (
            _author, type, CODE_URL + data.get('url'), data.get('ref'),
            CODE_URL + _project_url, _project)
    elif data['type'] == 'push':
        type = 'pushed'
        _project = data.get('repo_name')
        _project_url = "/%s" % _project
        _project = _project + ":" + data.get('branch')
        return "%s %s <a href=\"%s\">%s</a>" % ("someone",
                                                type,
                                                CODE_URL + _project_url,
                                                _project)
    return ''
