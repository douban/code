# -*- coding: utf-8 -*-

from __future__ import absolute_import
from datetime import datetime, timedelta
import itertools
import json
import os

from vilya.models.badge import Badge
from vilya.models import badge_timeline
from vilya.models.user import User
from vilya.libs.template import st

_q_exports = ['fetch_new', 'all', 'timeline', 'badges', 'items', 'count',
              'add']


def fetch_new(request):
    user = request.user
    if user:
        return json.dumps([{'bid': str(b.id)} for b in user.get_new_badges()])
    return ''


def all(request):
    user = request.user
    badges = Badge.get_all_badges()
    return st('badge/all.html', **locals())


def timeline(request):
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    return st('badge/timeline.html', **locals())


def badges(request):
    return json.dumps(badge_timeline.get_all_badges())


def items(request):
    index = int(request.get_form_var('ind', default=0))
    increment = int(request.get_form_var('inc', default=10))
    name = request.get_form_var('n', default='')
    item_list = badge_timeline.get_all_items(index, increment, name)
    item_list = [list(item) + [User(item[1]).avatar_url] for item in item_list]
    items = []
    for k, g in itertools.groupby(item_list, lambda row: row[3].date()):
        items.append(list(g))
    datehandler = lambda obj: obj.isoformat(
    ) if isinstance(obj, datetime) else None
    return json.dumps(items, default=datehandler)


def count(request):
    name = request.get_form_var('n', default='')
    return json.dumps(badge_timeline.get_item_count(name))


def add(request):
    if request.method == 'POST':
        name = request.get_form_var('name', '').strip()
        found = Badge.get_by_name(name)
        if found:
            return request.redirect('/badge/%s/' % found.id)

        summary = request.get_form_var('summary')
        filename = request.get_form_var("picfile").tmp_filename
        content = open(filename).read()

        new = Badge.add(name, summary)
        root = os.environ['DAE_APPROOT']
        pic_path = '%s/hub/static/img/badges/%s.png' % (root, new.id)
        open(pic_path, 'w').write(content)

        return request.redirect('/badge/%s/' % new.id)
    return st('badge/add.html', request=request)


class BadgeUI(object):
    _q_exports = ['people']

    def __init__(self, badge):
        self.badge = badge

    def _q_index(self, request):
        current_user = request.user
        badge = self.badge
        items = badge.get_awarded_items()
        users = [User(item.item_id) for item in items]
        return st('badge/badge.html', **locals())

    def people(self, request):
        current_user = request.user
        badge = self.badge
        if not current_user:
            return request.redirect('/badge/%s/' % badge.id)
        if current_user.name not in ['liwanjin', 'xutao']:
            return request.redirect('/badge/%s/' % badge.id)
        if request.method != 'POST':
            return request.redirect('/badge/%s/' % badge.id)
        name = request.get_form_var('name')
        reason = request.get_form_var('reason')
        if not name:
            return request.redirect('/badge/%s/' % badge.id)
        if not User.check_exist(name):
            return request.redirect('/badge/%s/' % badge.id)
        badge.award(name, reason=reason)
        return request.redirect('/badge/%s/' % badge.id)


def _q_lookup(request, id):
    b = Badge.get(id)
    if b:
        return BadgeUI(b)
