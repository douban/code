# -*- coding: utf-8 -*-

import os
import json
import itertools
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from vilya.libs.template import st


def fetch_new(request):
    user = request.user
    if user:
        return HttpResponse(json.dumps([{'bid': str(b.id)} for b in user.get_new_badges()]))
    return HttpResponse('')


def all(request):
    from vilya.models.badge import Badge
    user = request.user
    badges = Badge.get_all_badges()
    return HttpResponse(st('badge/all.html', **locals()))


def timeline(request):
    from datetime import datetime, timedelta
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    return HttpResponse(st('badge/timeline.html', **locals()))


def badges(request):
    from vilya.models import badge_timeline
    return HttpResponse(json.dumps(badge_timeline.get_all_badges()))


def items(request):
    from vilya.models import badge_timeline
    from datetime import datetime
    from vilya.models.user import User
    index = int(request.GET.get('ind', 0))
    increment = int(request.GET.get('inc', 10))
    name = request.GET.get('n', '')
    item_list = badge_timeline.get_all_items(index, increment, name)
    item_list = [list(item) + [User(item[1]).avatar_url] for item in item_list]
    items = []
    for k, g in itertools.groupby(item_list, lambda row: row[3].date()):
        items.append(list(g))
    datehandler = lambda obj: obj.isoformat(
    ) if isinstance(obj, datetime) else None
    return HttpResponse(json.dumps(items, default=datehandler))


def count(request):
    from vilya.models import badge_timeline
    name = request.GET.get('n', '')
    return HttpResponse(json.dumps(badge_timeline.get_item_count(name)))


def add(request):
    from vilya.models.badge import Badge
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        found = Badge.get_by_name(name)
        if found:
            return HttpResponseRedirect('/badge/%s/' % found.id)

        summary = request.POST.get('summary')
        filename = request.POST.get("picfile").tmp_filename
        content = open(filename).read()

        new = Badge.add(name, summary)
        # FIXME(xutao) upload dir
        root = os.environ['DAE_APPROOT']
        pic_path = '%s/hub/static/img/badges/%s.png' % (root, new.id)
        open(pic_path, 'w').write(content)

        return HttpResponseRedirect('/badge/%s/' % new.id)
    return HttpResponse(st('badge/add.html', request=request))


def badge_index(request, id):
    from vilya.models.badge import Badge
    from vilya.models.user import User
    badge = Badge.get(id)
    current_user = request.user
    items = badge.get_awarded_items()
    users = [User(item.item_id) for item in items]
    return HttpResponse(st('badge/badge.html', **locals()))


def badge_people(request, id):
    from vilya.models.badge import Badge
    from vilya.models.user import User
    current_user = request.user
    badge = Badge.get(id)
    if not current_user:
        return HttpResponseRedirect('/badge/%s/' % badge.id)
    if request.method != 'POST':
        return HttpResponseRedirect('/badge/%s/' % badge.id)
    name = request.POST.get('name')
    reason = request.POST.get('reason')
    if not name:
        return HttpResponseRedirect('/badge/%s/' % badge.id)
    if not User.check_exist(name):
        return HttpResponseRedirect('/badge/%s/' % badge.id)
    badge.award(name, reason=reason)
    return HttpResponseRedirect('/badge/%s/' % badge.id)
