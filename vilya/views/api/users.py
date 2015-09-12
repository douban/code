# -*- coding: utf-8 -*-
import time
from datetime import datetime
import dateutil.parser

from quixote.errors import TraversalError

from vilya.models.user import User
from vilya.models.ticket import Ticket
from vilya.models.gist import Gist, PAGE_LIMIT, gist_detail
from vilya.models.project import CodeDoubanProject
from vilya.models.contributions import UserContributions
from vilya.models.feed import get_user_feed, get_user_inbox
from vilya.models.timeline import format_timeline
from vilya.models.pull import PullRequest
from vilya.models.user_issue import UserIssue
from vilya.views.api.utils import api_list_user, jsonize

_q_exports = []


def _q_lookup(request, name):
    return UserUI(name)


class UserUI(object):
    _q_exports = ['gists', 'projects', 'timeline', 'followers', 'following',
                  'activities', 'contributions', 'contribution_detail',
                  'issues']

    def __init__(self, name):
        name = name.strip()
        self.user = User(name) if name else None
        if not self.user:
            raise TraversalError()

    def __call__(self, request):
        return self._index(request)

    @jsonize
    def _index(self, request):
        user = self.user
        dic = user.as_dict()
        if request.user and request.user.name != user.name:
            dic["following"] = request.user.is_following(user.name)
            dic["be_followed"] = user.is_following(request.user.name)
        dic["projects_count"] = CodeDoubanProject.count_by_owner_id(
            user.username)
        return dic

    def _q_index(self, request):
        return self._index(request)

    def _q_access(self, request):
        request.response.set_content_type('application/json; charset=utf-8')

    @jsonize
    def projects(self, request):
        projects = CodeDoubanProject.gets_by_owner_id(self.user.username)
        data = []
        without_commits = request.get_form_var('without_commits')
        for project in projects:
            data.append(project.get_info(without_commits))
        return data

    @jsonize
    def gists(self, request):
        owner_id = self.user.name
        page = request.get_form_var('page', '1')
        page = page and page.isdigit() and int(page) or 1
        start = (abs(page) - 1) * PAGE_LIMIT
        gists = Gist.gets_by_owner(owner_id, start=start)
        ret = [gist_detail(g) for g in gists]
        return ret

    @jsonize
    def issues(self, request):
        state = request.get_form_var('state', 'open')
        owner_id = self.user.name
        issues = UserIssue.gets_by_creator_id(owner_id, state=state)
        return [i.as_dict() for i in issues if i.target_type == 'project']

    @jsonize
    def timeline(self, request):
        user = request.user
        if not user:
            return []
        timestamp = request.get_form_var('timestamp')
        count = request.get_form_var('count') or 15
        start = request.get_form_var('start') or 0
        start = int(start)
        count = int(count)
        if timestamp:
            actions = get_user_inbox(
                self.user.username).get_actions_by_timestamp(max=timestamp)
            actions = actions[:count]
        else:
            actions = get_user_inbox(
                self.user.username).get_actions(start, start + count)
        data = []
        for action in actions:
            data.append(format_timeline(action))
        return data

    @jsonize
    def followers(self, request):
        user = self.user
        followers = user.get_followers()
        return api_list_user(followers)

    @jsonize
    def following(self, request):
        user = self.user
        following = user.get_following()
        return api_list_user(following)

    @jsonize
    def activities(self, request):
        start = request.get_form_var('start', '0')
        limit = request.get_form_var('count', '20')
        if start.isdigit() and limit.isdigit():
            start = int(start)
            limit = int(limit)
        else:
            start = 0
            limit = 20
        activities = get_user_feed(self.user.username).get_actions(
            start, limit)
        return [format_timeline(activity) for activity in activities]

    @jsonize
    def contributions(self, request):
        res = {}
        days = int(request.get_form_var('days', 31))
        for date_, contribution in UserContributions.get_by_user(
                self.user.name, days=days).iteritems():
            timestamp = time.mktime(
                datetime.strptime(date_, '%Y-%m-%d').timetuple())
            score = contribution[0]
            res.setdefault(timestamp, score)
        return res

    @jsonize
    def contribution_detail(self, request):
        req_date = request.get_form_var('date')
        if not req_date:
            return {"error": "No datetime"}
        try:
            req_date = dateutil.parser.parse(req_date).astimezone(
                dateutil.tz.tzoffset('EST', 8 * 3600))
        except ValueError:
            return {"error": "Invalid date"}
        contributions = UserContributions.get_by_date(self.user.name, req_date)
        owned = contributions.get('owned_tickets')
        commented = contributions.get('commented_tickets')
        pullreqs = [Ticket.get(id_).as_dict() for id_ in owned]
        participated = [Ticket.get(comment[0]).as_dict()
                        for comment in commented]
        return {"pull requests": pullreqs,
                "participated": participated}


def get_ticket_info(ticket):
    info = PullRequest.get_by_proj_and_ticket(ticket.project_id,
                                              ticket.ticket_number).as_dict()
    return info
