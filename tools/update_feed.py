# -*- coding: utf-8 -*-

import json
from datetime import datetime
from vilya.libs.rdstore import rds
from vilya.models.utils import (
    CJsonEncoder,
)
from vilya.models.feed import (
    get_user_feed as get_user_feed_v2,
    get_user_inbox as get_user_inbox_v2,
    get_public_feed as get_public_feed_v2,
    get_team_feed as get_team_feed_v2,
)
from vilya.models.team import Team


# update feed data from v1 to v2
MAX_ACTIONS_COUNT = 1009  # Happy Number
RDS_USER_INBOX_KEY = 'feed:private:user:v1:%s'
RDS_USER_FEED_KEY = 'feed:public:user:v1:%s'
RDS_PUBLIC_FEED_KEY = 'feed:public:everyone:v1'
RDS_TEAM_FEED_KEY = 'feed:public:team:v1:%s'


class Feed(object):
    def __init__(self, db_key):
        self.db_key = db_key

    def __repr__(self):
        return '%s (%s)' % (self.__class__, self.db_key)

    @classmethod
    def get(cls, db_key):
        return cls(db_key=db_key)

    def add_action(self, action_data):
        data = json.dumps(action_data, cls=CJsonEncoder)
        rds.lpush(self.db_key, data)
        rds.ltrim(self.db_key, 0, MAX_ACTIONS_COUNT)

    def get_actions(self):
        data = rds.lrange(self.db_key, 0, MAX_ACTIONS_COUNT)
        return [json.loads(d) for d in data]


def get_user_inbox(user):
    return Feed.get(db_key=RDS_USER_INBOX_KEY % user)


def get_user_feed(user):
    return Feed.get(db_key=RDS_USER_FEED_KEY % user)


def get_public_feed():
    return Feed.get(db_key=RDS_PUBLIC_FEED_KEY)


def get_team_feed(team):
    return Feed.get(db_key=RDS_TEAM_FEED_KEY % team)


def main():
    public_feed = get_public_feed()
    public_feed_v2 = get_public_feed_v2()
    feeds = public_feed.get_actions()
    for feed in feeds:
        date = datetime.strptime(feed['date'], "%Y-%m-%d %H:%M:%S")
        feed['date'] = date
        public_feed_v2.add_action(feed)
    print "updated %s public feeds." % len(feeds)

    teams = Team.gets()
    for team in teams:
        team_feed = get_team_feed(team.id)
        team_feed_v2 = get_team_feed_v2(team.id)
        feeds = team_feed.get_actions()
        for feed in feeds:
            date = datetime.strptime(feed['date'], "%Y-%m-%d %H:%M:%S")
            feed['date'] = date
            team_feed_v2.add_action(feed)
        print "updated %s team %s feeds." % (len(feeds), team.name)

    user_inbox_keys = rds.keys('feed:private:user:v1:*')
    for key in user_inbox_keys:
        _, _, _, _, user = key.split(':')
        user_feed = get_user_inbox(user)
        user_feed_v2 = get_user_inbox_v2(user)
        feeds = user_feed.get_actions()
        for feed in feeds:
            date = datetime.strptime(feed['date'], "%Y-%m-%d %H:%M:%S")
            feed['date'] = date
            user_feed_v2.add_action(feed)
        print "updated %s user %s inbox feeds." % (len(feeds), user)

    user_feed_keys = rds.keys('feed:public:user:v1:*')
    for key in user_feed_keys:
        _, _, _, _, user = key.split(':')
        user_feed = get_user_feed(user)
        user_feed_v2 = get_user_feed_v2(user)
        feeds = user_feed.get_actions()
        for feed in feeds:
            date = datetime.strptime(feed['date'], "%Y-%m-%d %H:%M:%S")
            feed['date'] = date
            user_feed_v2.add_action(feed)
        print "updated %s user %s feeds." % (len(feeds), user)


if __name__ == "__main__":
    main()
