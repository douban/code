# encoding: utf-8

from urlparse import urlparse
import json
import urllib
import urllib2

import requests

from vilya.config import DOMAIN
from vilya.models.pull import PullRequest
from vilya.models.ticket import Ticket
from vilya.libs.push_notification import send_alert


def __enter__(data):
    author = data.get('author')
    type_ = data.get('type')
    ticket = data.get('ticket')
    pullreq = data.get('pullreq')
    hooks = data.get('hooks')
    hook_urls = [hook.url for hook in hooks] if hooks else []

    from_proj = pullreq.from_proj
    to_proj = pullreq.to_proj

    from_proj_dict = {
        'url': from_proj.url,
        'name': from_proj.name,
        'description': from_proj.summary,
        'from_ref': pullreq.from_ref,
        'owner': {'name': from_proj.owner_name}
    }

    to_ref_dict = {
        'url': to_proj.url,
        'name': to_proj.name,
        'description': to_proj.summary,
        'from_ref': pullreq.to_ref,
        'owner': {'name': to_proj.owner_name}
    }

    author_dict = {'name': author.name, 'url': author.url}

    rdata = {
        'type': type_,
        'id': ticket.ticket_id,
        'author': author_dict,
        'from_proj': from_proj_dict,
        'to_ref': to_ref_dict,
        'url': ticket.url,
        'title': ticket.title,
    }

    # FIXME: content 没定义，而且照目前的代码看，type_ in ('pr_merge', None), see views/uis/pull.py
    if type_ == 'pr_opened':
        rdata.update({
            'title': data.get('title'),
            'body': data.get('body'),
            'ticket_id': data.get('ticket').id,
        })
    elif type_ == 'pr_merge':
        rdata.update({
            'commit_message': data.get('commit_message'),
        })
    elif type_ == 'pr_closed':
        rdata.update({
            'content': '',
        })
    # now... data is (hook_urls, rdata)
    return hook_urls, rdata


def async_pr_hooks(args):
    hooks, data = args
    json_data = json.dumps(data)
    for hook in hooks:
        url = urlparse(hook)

        if url.hostname and url.hostname.endswith('.slack.com'):
            slack_data = gen_slack_incoming_webhooks_data(data)
            s = requests.Session()
            try:
                s.post(hook, data=json.dumps(slack_data), timeout=30)
            except Exception as e:
                print "%s => %s" % (hook, e)
        elif data.get('type') == 'pr_opened' and url.hostname and \
             url.hostname.startswith('telchar'):
            telchar_data = gen_telchar_data(data)
            try:
                requests.post(hook, data=telchar_data, timeout=30)
            except Exception as e:
                print "%s => %s" % (hook, e)
        else:
            try:
                u = urllib2.urlopen(hook, urllib.urlencode({'data': json_data}))
                u.read()
                u.close()
            except urllib2.URLError as e:
                print "%s => %s" % (hook, e)


def async_push_notif(args):
    hooks, data = args
    msg = data.get('title')
    to_proj = data.get('to_ref')
    if to_proj.get('name') == 'iCode':
        send_alert(msg)


def gen_telchar_data(data):
    ticket_id = data.get('ticket_id')
    ticket = Ticket.get(ticket_id)
    pullreq = PullRequest.get_by_proj_and_ticket(
        ticket.project.id, ticket.ticket_id)
    fork_from = pullreq.from_proj.fork_from
    fork_from = pullreq.from_proj.get(fork_from).url if fork_from else None
    return {
        'ticket_id': ticket.ticket_id,
        'fork_from': fork_from,
        'url': pullreq.from_proj.url,
        'to_sha': pullreq.to_sha,
        'from_sha': pullreq.from_sha
    }


def gen_slack_incoming_webhooks_data(data):
    type_ = data.get('type')
    action_text_mapping = {
        'pr_opened': 'opened',
        'pr_merge': 'merged',
        'pr_closed': 'closed',
    }
    if type_ not in action_text_mapping:
        return {}

    text = data.get('text', '')
    author_dict = data.get('author', {})
    author_url = author_dict.get('url', '')
    author_name = author_dict.get('name', '')

    pr_url = data.get('url', '')
    pr_id = data.get('id', '')
    pr_title = data.get('title', '')

    to_ref_dict = data.get('to_ref', {})
    to_proj_url = to_ref_dict.get('url', '')
    to_proj_name = to_ref_dict.get('name', '')

    author_link = '<{0}{1}|{2}>'.format(DOMAIN, author_url, author_name)
    pr_link = '<{0}{1}|#{2} {3}>'.format(DOMAIN, pr_url, pr_id, pr_title)
    to_proj_link = '<{0}{1}|{2}>'.format(DOMAIN, to_proj_url, to_proj_name)

    action_text = action_text_mapping.get(type_)
    text = 'Pull Request {0} on {1} is {2} by {3}'.format(
        pr_link, to_proj_link, action_text, author_link)

    data = {
        'text': text,
        'username': 'Code',
    }

    return data
