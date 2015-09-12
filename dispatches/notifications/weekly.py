#!/usr/bin/env python
# encoding: utf-8

from vilya.libs.mailer import Mail, MailContext
from vilya.libs.date import (
    get_current_monday, get_last_monday,
    get_current_sunday, get_last_sunday)
from dispatches.notifications import NotificationDispatcher
from vilya.models.team import Team


class Dispatcher(NotificationDispatcher):

    def __init__(self, data):
        NotificationDispatcher.__init__(self, data)
        self._team_id = data.get('team_id')
        self._last_week = data.get('last_week')
        self._team = Team.get(self._team_id)

    @property
    def msgs(self):
        return [self.mail]

    @property
    def mail_receivers(self):
        toaddrs = Mail.addrs_by_usernames(self._team.user_ids)
        ccaddrs = ["xutao@douban.com"]
        return toaddrs, ccaddrs

    @property
    def mail(self):
        if self._last_week:
            timestamp = get_last_monday(timestamp=True)
            monday = get_last_monday()
            sunday = get_last_sunday()
        else:
            timestamp = get_current_monday(timestamp=True)
            monday = get_current_monday()
            sunday = get_current_sunday()
        changes = []
        projects = self._team.projects
        for project in projects:
            commits = project.repo.get_commits("HEAD", since=int(timestamp),
                                               no_merges=True)
            changes.append(dict(project=project, commits=commits))
        lines = []
        toaddrs, ccaddrs = self.mail_receivers
        mail = Mail("Code Team Weekly",
                    to=toaddrs,
                    cc=ccaddrs,
                    context=MailContext('weekly', data={"lines": lines,
                                                        "changes": changes,
                                                        "team": self._team,
                                                        "sunday": sunday,
                                                        "monday": monday}),
                    big=True)
        return mail
