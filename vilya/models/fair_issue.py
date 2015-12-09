# -*- coding: utf-8 -*-
from __future__ import absolute_import

from urlparse import urlparse

from vilya.libs.store import store, mc, cache, IntegrityError
from vilya.models.issue import Issue, get_issue_by_id_and_state
from vilya.models.tag import TAG_TYPE_FAIR_ISSUE

MC_KEY_ISSUE_PLEDGED = 'issue_pledged:%s'


class FairIssue(Issue):
    target_type = 'fair'
    tag_type = TAG_TYPE_FAIR_ISSUE
    provided_features = ['team-issue', 'fair-issue', 'related-projects',
                         'pledge']

    def __init__(self, id, team_id, issue_id, number, title=None,
                 creator=None, assignee=None, closer=None,
                 created_at=None, updated_at=None, closed_at=None,
                 type=''):
        Issue.__init__(self, issue_id, title, creator, assignee, closer,
                       created_at, updated_at, closed_at, self.target_type)
        self.number = self.id
        from vilya.models.fair import FAIR_ID
        self.team_id = FAIR_ID

    @property
    def url(self):
        return '/fair/%s/' % self.issue_id

    @property
    def target(self):
        from vilya.models.fair import get_fair
        return get_fair()

    @classmethod
    def add(cls, title, description, creator, number=None,
            team=None, project=None, assignee=None, closer=None,
            created_at=None, updated_at=None, closed_at=None):
        issue = Issue.add(title, description, creator, assignee=assignee,
                          closer=closer, type='fair', target_id=team)
        if issue:
            number = issue.id
            '''
            team_issue_id = store.execute(
                'insert into team_issues (team_id, issue_id, number) '
                'values (%s, %s, %s)',
                (team, issue.id, number))
            store.commit()
            '''
            return cls(issue.id, team, issue.id, number, title, creator,
                       assignee, closer, issue.created_at, issue.updated_at)

    @classmethod
    def get(cls, team_id, issue_id=None, number=None):
        # FIXME: dirty hack. 需要统一子类和基类的get方法
        if number:
            issue_id = number
        return Issue.get_cached_issue(issue_id)

    @classmethod
    def get_by_issue_id(cls, issue_id):
        issue = Issue.get(issue_id)
        if issue:
            from vilya.models.fair import FAIR_ID
            return cls(id, FAIR_ID, issue.id, issue.id, issue.title,
                       issue.creator_id, issue.assignee_id, issue.closer_id,
                       issue.created_at, issue.updated_at, issue.closed_at,
                       issue.type)

    @classmethod
    def gets_by_issue_ids(cls, issue_ids, state):
        fair_issues = []
        for issue_id in issue_ids:
            fair_issue = get_issue_by_id_and_state(issue_id, state)
            if fair_issue:
                fair_issues.append(fair_issue)
        fair_issues.sort(key=lambda x: x.updated_at, reverse=True)
        return fair_issues

    def add_related_project(self, repo_url):
        info = urlparse(repo_url)
        project_name = info.path.strip('/')
        from vilya.models.project import CodeDoubanProject
        prj = CodeDoubanProject.get_by_name(project_name)
        if prj not in self.related_projects:
            store.execute('insert into issue_related_projects '
                          '(issue_id, project_id) values(%s, %s)',
                          (self.issue_id, prj.id))
            store.commit()

    def delete_related_project(self, prj):
        store.execute('delete from issue_related_projects '
                      'where issue_id=%s and project_id=%s',
                      (self.issue_id, prj.id))
        store.commit()

    @property
    def related_projects(self):
        rs = store.execute('select project_id from issue_related_projects '
                           'where issue_id=%s', (self.issue_id,))
        prj_ids = [id for (id, ) in rs]
        from vilya.models.project import CodeDoubanProject
        return CodeDoubanProject.gets(prj_ids)

    @property
    def pledged(self):
        from vilya.models.user import User
        return [(User(user_id), amount)
                for user_id, amount, time in self.get_pledged()]

    @property
    def pledged_amount(self):
        amounts = [amount for user_id, amount, time in self.get_pledged()]
        return sum(amounts)

    def pledged_by(self, user):
        for auser, amount in self.pledged:
            if auser == user:
                return amount
        return 0

    @cache(MC_KEY_ISSUE_PLEDGED % '{self.issue_id}')
    def get_pledged(self):
        rs = store.execute('select user_id, amount, created_at '
                           'from issue_pledge '
                           'where issue_id=%s ',
                           (self.issue_id,))
        return rs

    def update_pledge(self, user, amount):
        try:
            store.execute('insert into issue_pledge '
                          '(issue_id, user_id, amount) '
                          'values (%s, %s, %s)',
                          (self.issue_id, user.name, amount))
        except IntegrityError:
            store.execute('update issue_pledge '
                          'set amount=%s '
                          'where issue_id=%s and user_id=%s',
                          (amount, self.issue_id, user.name))
        store.commit()
        mc.delete(MC_KEY_ISSUE_PLEDGED % self.issue_id)
