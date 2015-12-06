# -*- coding: utf-8 -*-

from __future__ import absolute_import

from quixote.errors import TraversalError
import time
from vilya.libs.template import st
from vilya.libs.validators import check_user_id
import itertools
from datetime import datetime, timedelta
import dateutil.parser

from vilya.views.util import jsonize
from vilya.models.project import CodeDoubanProject
from vilya.models.user import User
from vilya.models.badge import Badge
from vilya.models.recommendation import Recommendation
from vilya.models.contributions import UserContributions
from vilya.models.feed import get_user_feed
from vilya.models.team import Team
from vilya.models.ticket import Ticket
from vilya.models.user import judge_user

_q_exports = []


def _q_lookup(request, name):
    # FIXME: check user name.
    if judge_user(name) == "team":
        return request.redirect('/teams/%s/' % name)
    else:
        return UserUI(request, name)


class UserUI:
    _q_exports = ['badges', 'follow', 'unfollow', 'following', 'followers',
                  'add_rec', 'praises', 'contributions', 'contribution_detail']

    FOLLOW_LIST_USER_COUNT = 24

    def __init__(self, request, name):
        self.name = name

    def _q_access(self, request):
        if not check_user_id(self.name):
            raise TraversalError('not a valid user id')

    def _q_index(self, request):
        name = self.name
        your_projects = CodeDoubanProject.get_projects(owner=name,
                                                       sortby='lru')
        actions = get_user_feed(name).get_actions(0, 20)
        user = User(name)
        teams = Team.get_by_user_id(user.name)
        badge_items = user.get_badge_items()
        followers_count = user.followers_count
        following_count = user.following_count
        if user and user.username == name and user.get_new_badges():
            user.clear_new_badges()
        return st('people.html', **locals())

    @jsonize
    def follow(self, request):
        name = self.name
        user = request.user
        if not user:
            return {"action": 0, "msg": "Please login first."}
        username = user.username
        if username == name:
            action = 0
            msg = "You can't follow yourself"
        else:
            user.follow(name)
            action = 1
            msg = "success"
        return {"action": action, "msg": msg}

    @jsonize
    def unfollow(self, request):
        name = self.name
        user = request.user
        if not user:
            return {"action": 0, "msg": "Please login first."}
        username = user.username
        if username == name:
            action = 0
            msg = "You can't unfollow yourself"
        else:
            User(username).unfollow(name)
            action = -1
            msg = "success"
        return {"action": action, "msg": msg}

    def following(self, request):
        name = self.name
        list_type = "following"
        user_list = User(name).get_following()
        return self.follow_list(request, list_type, user_list)

    def followers(self, request):
        name = self.name
        list_type = "followers"
        user_list = User(name).get_followers()
        return self.follow_list(request, list_type, user_list)

    def follow_list(self, request, list_type, user_list):
        name = self.name
        page = int(request.get_form_var('page', 1))
        count = len(user_list)
        start = self.FOLLOW_LIST_USER_COUNT * (page - 1)
        n_pages = count / self.FOLLOW_LIST_USER_COUNT + 1
        user_list = user_list[start:(start + self.FOLLOW_LIST_USER_COUNT)]
        current_user = user = request.user
        current_user_following = current_user.get_following() \
                                 if current_user else []
        return st('follow-list.html', **locals())

    def badges(self, request):
        name = self.name
        badge_items = Badge.get_badge_items()
        _date_badge_items = [i for i in badge_items if i.date]
        items_groupby_date = itertools.groupby(
            _date_badge_items, lambda badge_item: badge_item.date.date())
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)
        return st('badge/timeline.html', **locals())

    def add_rec(self, request):
        name = self.name
        if request.method == "POST":
            content = request.get_form_var('content')
            user = request.user
            r = Recommendation.add(
                from_user=user.name, to_user=self.name, content=content)
            return request.redirect('/people/%s/praises' % name)
        return st('people_add_rec.html', **locals())

    def praises(self, request):
        name = self.name
        recs = Recommendation.gets_by_user(name)
        return st('people_recs.html', **locals())

    @jsonize
    def contributions(self, request):
        res = {}
        for date_, contribution in UserContributions.get_by_user(
                self.name).iteritems():
            timestamp = time.mktime(
                datetime.strptime(date_, '%Y-%m-%d').timetuple())
            score = contribution[0]
            res.setdefault(timestamp, score)
        return res

    def contribution_detail(self, request):
        req_date = request.get_form_var('date')
        if req_date:
            try:
                req_date = dateutil.parser.parse(
                    req_date).astimezone(dateutil.tz.tzoffset('EST', 8*3600))
            except ValueError as e:
                return ""
            contributions = UserContributions.get_by_date(self.name, req_date)
            owned = contributions.get('owned_tickets')
            commented = contributions.get('commented_tickets')
            owned_tickets = filter(None, [Ticket.get(id_) for id_ in owned])
            commented_tickets = filter(None, [Ticket.get(comment[0])
                                              for comment in commented])
            return st('people_contribution_detail.html', **locals())
        return ""
