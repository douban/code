#!/usr/bin/env python
# encoding: utf-8

from vilya.config import DOMAIN
from dispatches.notifications import NotificationDispatcher
from vilya.libs.text import get_mentions_from_text
from vilya.models.actions.recommend import Recommend as RecommendAction
from vilya.models.notification import Notification
from vilya.models.feed import FeedMsg


class Dispatcher(NotificationDispatcher):
    def __init__(self, data):
        NotificationDispatcher.__init__(self, data)
        self._recommend = data.get('recommend')

    @property
    def msgs(self):
        return [self.noti, self.feedmsg]

    @property
    def noti_receivers(self):
        receivers = set()
        receivers.add(self._recommend.to_user)
        mentions = set(get_mentions_from_text(self._recommend.content))
        return receivers | mentions

    @property
    def noti_data(self):
        recommend = self._recommend
        url = ('%s/people/%s/praises' % (DOMAIN, recommend.to_user))
        action = RecommendAction(recommend.from_user, recommend.created,
                                 recommend, url)
        return action.to_dict()

    @property
    def noti(self):
        return Notification(self._uid, self.noti_receivers, self.noti_data)

    @property
    def feedmsg(self):
        sender = self._recommend.from_user
        return FeedMsg(sender, [self._recommend.to_user],
                       data=self.noti_data)
