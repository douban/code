# -*- coding: utf-8 -*-

from __future__ import absolute_import
from vilya.libs.store import store
from vilya.models.issue import Issue, get_issue_by_id_and_state
from vilya.models.tag import TAG_TYPE_TEAM_ISSUE


class TICounter(object):
    """Team Issue Counter"""

    @classmethod
    def incr(cls, team_id, count=None):
        if count >= 0:
            sql = ("insert into team_issue_counters (team_id, counter) "
                   "values (%s, LAST_INSERT_ID(%s)) on duplicate key "
                   "update counter = LAST_INSERT_ID(%s)")
            id = store.execute(sql, (team_id, count, count))
        else:
            sql = ("insert into team_issue_counters (team_id, counter) "
                   "values (%s, LAST_INSERT_ID(%s)) on duplicate key "
                   "update counter = LAST_INSERT_ID(counter + 1)")
            id = store.execute(sql, (team_id, 1))
        store.commit()
        return id


class TeamIssue(Issue):
    target_type = 'team'
    tag_type = TAG_TYPE_TEAM_ISSUE
    provided_features = ['team-issue', 'vote']

    def __init__(self, id, team_id, issue_id, number, title=None,
                 creator=None, assignee=None, closer=None,
                 created_at=None, updated_at=None, closed_at=None, type=''):
        Issue.__init__(self, issue_id, title,
                       creator, assignee, closer,
                       created_at, updated_at, closed_at, type=type,
                       target_id=team_id)
        self.id = id
        self.team_id = team_id
        self.issue_id = issue_id
        self.number = number

    def __repr__(self):
        return '<TeamIssue(id=%s, team=%s, number=%s)>' % (self.issue_id,
                                                           self.team_id,
                                                           self.number)

    @property
    def url(self):
        return '%sissues/%s/' % (self.target.url, self.number)

    @classmethod
    def add(cls, title, description, creator, number=None,
            team=None, project=None, assignee=None, closer=None,
            created_at=None, updated_at=None, closed_at=None):
        issue = Issue.add(title, description, creator, assignee=assignee,
                          closer=closer, type=cls.target_type, target_id=team)
        if issue and team:
            number = TICounter.incr(team, number)
            team_issue_id = store.execute(
                'insert into team_issues (team_id, issue_id, number) '
                'values (%s, %s, %s)',
                (team, issue.id, number))
            store.commit()
            return cls(team_issue_id, team, issue.id, number, title, creator,
                       assignee, closer, issue.created_at, issue.updated_at)

    @classmethod
    def get(cls, team_id, issue_id=None, number=None):
        sql = ("select id, team_id, issue_id, number from team_issues "
               "where team_id = %s ")
        params = [team_id]
        if issue_id:
            sql = sql + "and issue_id = %s "
            params.append(issue_id)
        if number:
            sql = sql + "and number = %s "
            params.append(number)
        rs = store.execute(sql, tuple(params))
        if rs and rs[0]:
            return cls(*rs[0])

    @property
    def target(self):
        from vilya.models.team import Team
        return Team.get(self.team_id)

    @classmethod
    def get_by_issue_id(cls, issue_id):
        sql = ("select id, team_id, issue_id, number from team_issues "
               "where issue_id = %s ")
        rs = store.execute(sql, (issue_id,))
        if rs and rs[0]:
            id, team_id, issue_id, number = rs[0]
            issue = Issue.get(issue_id)
            if issue:
                return cls(id, team_id, issue.id, number, issue.title,
                           issue.creator_id, issue.assignee_id,
                           issue.closer_id, issue.created_at, issue.updated_at,
                           issue.closed_at, issue.type)

    @classmethod
    def gets_by_issue_ids(cls, issue_ids, state):
        team_issues = []
        for issue_id in issue_ids:
            team_issue = get_issue_by_id_and_state(issue_id, state)
            if team_issue:
                team_issues.append(team_issue)
        team_issues.sort(key=lambda x: x.updated_at, reverse=True)
        return team_issues
