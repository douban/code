#!/usr/bin/env python
# encoding: utf-8

from vilya.config import DOMAIN
from dispatches.notifications import NotificationDispatcher
from vilya.libs.irc import IrcMsg
from vilya.models.actions.team_add_member import TeamAddMember
from vilya.models.notification import Notification


class Dispatcher(NotificationDispatcher):

    def __init__(self, data):
        NotificationDispatcher.__init__(self, data)
        self._sender = data.get('sender')
        self._identity = data.get('identity', '')
        self._team_uid = data.get('team_uid', '')
        self._team_name = data.get('team_name', '')
        self._receiver = data.get('receiver')

    @property
    def msgs(self):
        return [self.noti, self.ircmsg]

    @property
    def noti_data(self):
        url = '/hub/team/%s/' % self._team_uid,
        action = TeamAddMember(self._sender, self.now(), self._receiver,
                               self._team_name, self._identity, url)
        return action.to_dict()

    @property
    def receivers(self):
        return {self._receiver}

    @property
    def noti(self):
        return Notification(
            self._uid,
            self.receivers,
            self.noti_data)

    @property
    def ircmsg(self):
        url = DOMAIN + '/hub/team/%s' % (self._team_uid)
        msg = "%s add you as %s of team %s ( %s )" % (self._sender,
                                                      self._identity,
                                                      self._team_name,
                                                      url)
        return IrcMsg(self.receivers, msg)
