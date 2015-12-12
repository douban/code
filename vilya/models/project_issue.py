# -*- coding: utf-8 -*-

from __future__ import absolute_import

from vilya.libs.store import store, mc, cache
from vilya.models.issue import (
    Issue, get_issue_by_id_and_state,
    filter_issue_ids_by_score, filter_issue_ids_by_state)
from vilya.models.tag import TAG_TYPE_PROJECT_ISSUE
from vilya.models.issue_milestone import IssueMilestone
from vilya.config import DOMAIN
from vilya.models.issue import MC_KEY_ISSUES_DATA_BY_TARGET

MC_KEY_PROJECT_ISSUE_N = 'project_issue:v3:%s:%s:n'
MC_KEY_PROJECT_ISSUE_CREATOR_N = 'project_issue:v3:%s:%s:creator:%s:n'
MC_KEY_PROJECT_ISSUE_ASSIGNEE_N = 'project_issue:v3:%s:%s:assignee:%s:n'


class PICounter(object):
    """Project Issue Counter"""

    @classmethod
    def incr(cls, proj_id, count=None):
        if count >= 0:
            sql = ("insert into poject_issue_counters (project_id, counter) "
                   "values (%s, LAST_INSERT_ID(%s)) on duplicate key "
                   "update counter = LAST_INSERT_ID(%s)")
            id = store.execute(sql, (proj_id, count, count))
        else:
            sql = ("insert into project_issue_counters (project_id, counter) "
                   "values (%s, LAST_INSERT_ID(%s)) on duplicate key "
                   "update counter = LAST_INSERT_ID(counter + 1)")
            id = store.execute(sql, (proj_id, 1))
        store.commit()
        return id


class ProjectIssue(Issue):
    target_type = 'project'
    tag_type = TAG_TYPE_PROJECT_ISSUE
    provided_features = ['project-issue', 'vote', 'milestone']

    def __init__(self, id, project_id, issue_id, number, title=None,
                 creator=None, assignee=None, closer=None,
                 created_at=None, updated_at=None, closed_at=None, type=''):
        Issue.__init__(
            self, issue_id, title, creator, assignee, closer, created_at,
            updated_at, closed_at, type=type, target_id=project_id)
        self.id = id
        self.project_id = project_id
        self.issue_id = issue_id
        self.number = number

    def __repr__(self):
        return '<ProjectIssue(id=%s, prj=%s, number=%s)>' % (
            self.issue_id, self.project_id, self.number)

    @property
    def url(self):
        return '%sissues/%s/' % (self.target.url, self.number)

    def open(self):
        Issue.open(self)
        self.clear_cache()
        mc.delete(MC_KEY_PROJECT_ISSUE_N % (self.project_id, 'open'))

    def close(self, user_id):
        Issue.close(self, user_id)
        self.clear_cache()
        mc.delete(MC_KEY_PROJECT_ISSUE_N % (self.project_id, 'closed'))

    def assign(self, user_id):
        Issue.assign(self, user_id)
        self.clear_cache()
        mc.delete(MC_KEY_PROJECT_ISSUE_ASSIGNEE_N % (
            self.project_id, user_id, 'open'))
        mc.delete(MC_KEY_PROJECT_ISSUE_ASSIGNEE_N % (
            self.project_id, user_id, 'closed'))

    @classmethod
    def add(cls, title, description, creator, number=None,
            team=None, project=None, assignee=None, closer=None,
            created_at=None, updated_at=None, closed_at=None):
        issue = Issue.add(title, description, creator,
                          assignee=assignee, closer=closer,
                          type=cls.target_type, target_id=project)
        if issue and project:
            number = PICounter.incr(project, number)
            store.execute(
                'insert into project_issues (project_id, issue_id, number) '
                'values (%s, %s, %s) ',
                (project, issue.id, number))
            store.commit()
            mc.delete(MC_KEY_PROJECT_ISSUE_CREATOR_N % (
                project, creator, 'open'))
            mc.delete(MC_KEY_PROJECT_ISSUE_CREATOR_N % (
                project, creator, 'closed'))
            cls._clean_cache(project)
            return Issue.get_cached_issue(issue.id)

    @property
    def target(self):
        from vilya.models.project import CodeDoubanProject
        return CodeDoubanProject.get(self.project_id)

    @property
    def proj_name(self):
        from vilya.models.project import CodeDoubanProject
        return CodeDoubanProject.get(self.project_id).name

    def _tags_as_dict(self):
        tags = self.tags
        tag_names = []
        for t in tags:
            tag_names.append(t.name)
        return tag_names

    def _participants_as_dict(self):
        participants = self.participants
        participant_names = []
        for p in participants:
            participant_names.append(p.name)
        return participant_names

    def as_dict(self):
        d = {}
        project_name = self.target.__str__()
        d['url'] = "%s/api/%s/issues/%s" % (
            DOMAIN, project_name, self.number)
        d['html_url'] = "%s/%s/issues/%s/" % (
            DOMAIN, project_name, self.number)
        d['issue_id'] = self.issue_id
        d['number'] = self.number
        # 'self' does not contain informations like title, desc, etc.
        issue = self.get_by_issue_id(self.issue_id)
        d['title'] = issue.title
        d['project_id'] = self.target.id
        d['description'] = issue.description
        d['project'] = self.proj_name
        d['creator'] = issue.creator_id
        d['type'] = issue.type
        d['state'] = issue.state
        d['comments'] = self.comment_count
        d['state'] = issue.state
        participants = self._participants_as_dict()
        if participants:
            d['participants'] = participants
        tags = self._tags_as_dict()
        if tags:
            d['tags'] = tags
        if issue.assignee_id:
            d['assignee'] = issue.assignee_id
        if issue.closer_id:
            d['closer'] = issue.closer_id
        if issue.created_at:
            d['created_at'] = issue.created_at.strftime('%Y-%m-%dT%H:%M:%S')
        if issue.updated_at:
            d['updated_at'] = issue.updated_at.strftime('%Y-%m-%dT%H:%M:%S')
        if issue.closed_at:
            d['closed_at'] = issue.closed_at.strftime('%Y-%m-%dT%H:%M:%S')
        return d

    @classmethod
    def get(cls, project_id, issue_id=None, number=None):
        sql = ("select id, project_id, issue_id, number from project_issues "
               "where project_id = %s ")
        params = [project_id]
        if issue_id:
            sql = sql + "and issue_id = %s "
            params.append(issue_id)
        if number:
            sql = sql + "and number = %s "
            params.append(number)
        rs = store.execute(sql, tuple(params))
        if rs and rs[0]:
            return cls(*rs[0])

    @classmethod
    def get_by_issue_id(cls, issue_id):
        sql = ("select id, project_id, issue_id, number from project_issues "
               "where issue_id = %s ")
        rs = store.execute(sql, (issue_id,))
        if rs and rs[0]:
            id, project_id, issue_id, number = rs[0]
            issue = Issue.get(issue_id)
            if issue:
                return cls(
                    id, project_id, issue.id, number, issue.title,
                    issue.creator_id, issue.assignee_id, issue.closer_id,
                    issue.created_at, issue.updated_at, issue.closed_at,
                    issue.type)

    def delete_issue(self):
        issue = Issue.get(self.issue_id)
        issue.delete()

    @classmethod
    def get_by_proj_name_and_number(cls, proj_name, number):
        from vilya.models.project import CodeDoubanProject
        project = CodeDoubanProject.get_by_name(proj_name)
        project_issue = cls.get(project.id, number=number)
        issue_id = project_issue.issue_id
        return Issue.get_cached_issue(issue_id)

    @classmethod
    def _gets_by_issue_ids(cls, issue_ids, state):
        project_issues = []
        for issue_id in issue_ids:
            project_issue = get_issue_by_id_and_state(issue_id, state)
            if project_issue:
                project_issues.append(project_issue)
        project_issues.sort(key=lambda x: x.updated_at, reverse=True)
        return project_issues

    @classmethod
    def gets_by_issue_ids(cls, issue_ids, state=None, limit=20, start=0):
        project_issues = cls._gets_by_issue_ids(issue_ids, state)
        return project_issues[start:start + limit]

    @classmethod
    def get_n_by_issue_ids(cls, issue_ids, state=None):
        if not state:
            return len(issue_ids)
        else:
            issues = Issue.get_cached_issues(issue_ids)
            open_issues = [issue for issue in issues
                           if issue and not issue.is_closed]
            close_issues = [issue for issue in issues
                            if issue and issue.is_closed]
            if state == "open":
                return len(open_issues)
            else:
                return len(close_issues)

    @classmethod
    def _gets_by_issue_ids_and_people_id(cls, issue_ids, people_id,
                                         people_attr, state=None):
        project_issues = cls._gets_by_issue_ids(issue_ids, state)
        project_issues = [x for x in project_issues
                          if getattr(x, people_attr) == people_id]
        return project_issues

    @classmethod
    def gets_and_n_by_issue_ids_and_people(cls, issue_ids, people_id=None,
                                           people_attr=None, state=None,
                                           limit=25, start=0):
        ''' get issues and count by issue ids and people(creator/assignee) '''
        if people_id and people_attr:
            project_issues = cls._gets_by_issue_ids_and_people_id(
                issue_ids, people_id, people_attr, state)
        else:
            project_issues = cls._gets_by_issue_ids(issue_ids, state)
        return project_issues[start:start + limit], len(project_issues)

    @classmethod
    def gets_by_issue_ids_and_creator_id(cls, issue_ids, state, creator_id,
                                         limit=20, start=0):
        project_issues = cls._gets_by_issue_ids(issue_ids, state)
        project_issues = filter(
            lambda x: x.creator_id == creator_id, project_issues)
        return project_issues[start:start + limit]

    @classmethod
    def get_n_by_issue_ids_and_creator_id(cls, issue_ids, state, creator_id):
        project_issues = cls._gets_by_issue_ids(issue_ids, state)
        project_issues = filter(
            lambda x: x.creator_id == creator_id, project_issues)
        return len(project_issues)

    @classmethod
    def gets_by_issue_ids_and_assignee_id(cls, issue_ids, state, assignee_id,
                                          limit=20, start=0):
        project_issues = cls._gets_by_issue_ids(issue_ids, state)
        project_issues = filter(
            lambda x: x.assignee_id == assignee_id, project_issues)
        return project_issues[start:start + limit]

    @classmethod
    def get_n_by_issue_ids_and_assignee_id(cls, issue_ids, state, assignee_id):
        project_issues = cls._gets_by_issue_ids(issue_ids, state)
        project_issues = filter(
            lambda x: x.assignee_id == assignee_id, project_issues)
        return len(project_issues)

    @classmethod
    def get_count_by_project_id(cls, id, state=None):
        data = cls.get_data_by_target(id)
        if not state:
            return len(data)

        if state == "open":
            return len([i for (i, closer, _, _) in data if closer is None])
        else:
            return len([i for (i, closer, _, _) in data if closer is not None])

    @classmethod
    def _clean_cache(cls, id):
        # FIXME: update cache
        mc.delete(MC_KEY_PROJECT_ISSUE_N % (id, 'closed'))
        mc.delete(MC_KEY_PROJECT_ISSUE_N % (id, 'open'))

    def delete(self):
        issue = self.get_by_issue_id(self.issue_id)
        user_id = issue.assignee_id
        creator = issue.creator_id
        store.execute("delete from project_issues where id=%s", (self.id,))
        store.commit()
        mc.delete(MC_KEY_PROJECT_ISSUE_CREATOR_N % (
            self.project_id, creator, 'open'))
        mc.delete(MC_KEY_PROJECT_ISSUE_CREATOR_N % (
            self.project_id, creator, 'closed'))
        mc.delete(MC_KEY_PROJECT_ISSUE_ASSIGNEE_N % (
            self.project_id, user_id, 'open'))
        mc.delete(MC_KEY_PROJECT_ISSUE_ASSIGNEE_N % (
            self.project_id, user_id, 'closed'))
        mc.delete(MC_KEY_ISSUES_DATA_BY_TARGET % (
            self.target_type, self.project_id))
        self.delete_issue()
        self._clean_cache(id)

    @classmethod
    def _gets_by_project_id(cls, id, order='', state=None):
        '''get project issues by project id with order.'''

        data = cls.get_data_by_target(id)

        data = filter_issue_ids_by_state(data, state)
        data = filter_issue_ids_by_score(data, order)

        rs = [(id, issue_id) for (issue_id, closer, updated_at, rank_score)
              in data]

        return rs

    @classmethod
    def _get_ids_by_project_id(cls, id, order='', state=None):
        data = cls.get_data_by_target(id)

        data = filter_issue_ids_by_state(data, state)
        if order:
            data = filter_issue_ids_by_score(data, order)
        return [issue_id for (issue_id, _, _, _) in data]

    @classmethod
    def _get_issues_by_project_id(cls, id, state=None):
        '''get project issues by project id with order and issue state.'''
        ids = cls._get_ids_by_project_id(id, state=state)
        return Issue.get_cached_issues(ids)

    @classmethod
    def gets_by_project_id(cls, id, state=None, limit=25, start=0, order=''):
        '''get project issues by project id with order, issues state and
           limits.
        '''
        # TODO delete this method
        return cls.gets_by_target(id, state=state, order=order,
                                  limit=limit, start=start)

    @classmethod
    def get_count_by_project_ids(cls, ids, state=None):
        project_issues = []
        for id in ids:
            project_issues.extend(cls._get_ids_by_project_id(id, state=state))
        return len(project_issues)

    @classmethod
    def gets_by_project_ids(cls, project_ids, state=None, limit=25, start=0):
        data = []
        for id in project_ids:
            data.extend(cls.get_data_by_target(id))

        data = filter_issue_ids_by_state(data, state)
        data = filter_issue_ids_by_score(data, 'updated_at')
        data = data[start:start + limit]
        ids = [issue_id for (issue_id, _, _, _) in data]
        return Issue.get_cached_issues(ids)

    @classmethod
    def _gets_by_people_id(cls, project, people_id, state, type):
        ids = cls._get_ids_by_project_id(project, order='updated_at',
                                         state=state)
        issues = Issue.get_cached_issues(ids)
        issues = [issue for issue in issues
                  if getattr(issue, type) == people_id]
        return issues

    @classmethod
    def gets_and_n_by_people(cls, project_id, people_id=None,
                             people_attr=None, state=None, limit=25,
                             start=0, order=''):
        ''' get issues and count by project_id and people(creator/assignee) '''
        if people_id and people_attr:
            project_issues = cls._gets_by_people_id(project_id, people_id,
                                                    state, people_attr)
            return project_issues[start:start + limit], len(project_issues)
        else:
            # FIXME:
            project_issues = cls.gets_by_project_id(project_id, state, limit,
                                                    start, order)
            return project_issues, cls.get_count_by_project_id(
                project_id, state)

    @classmethod
    @cache(MC_KEY_PROJECT_ISSUE_ASSIGNEE_N % ('{id}', '{assignee}', '{state}'))
    def get_count_by_assignee_id(cls, id, assignee, state=None):
        return len(cls._gets_by_people_id(id, assignee, state, 'assignee_id'))

    @classmethod
    def gets_by_assignee_id(cls, project, assignee, state=None, limit=25,
                            start=0):
        project_issues = cls._gets_by_people_id(
            project, assignee, state, 'assignee_id')
        return project_issues[start:start + limit]

    @classmethod
    @cache(MC_KEY_PROJECT_ISSUE_CREATOR_N % ('{id}', '{creator}', '{state}'))
    def get_count_by_creator_id(cls, id, creator, state=None):
        return len(cls._gets_by_people_id(id, creator, state, 'creator_id'))

    @classmethod
    def gets_by_creator_id(cls, project, creator, state=None, limit=25,
                           start=0):
        project_issues = cls._gets_by_people_id(
            project, creator, state, 'creator_id')
        return project_issues[start:start + limit]

    @property
    @cache(MC_KEY_PROJECT_ISSUE_N % ('{self.project_id}', 'open'))
    def n_open_issues(self):
        return self.get_count_by_project_id(self.project_id, "open")

    @property
    @cache(MC_KEY_PROJECT_ISSUE_N % ('{self.project_id}', 'closed'))
    def n_closed_issues(self):
        return self.get_count_by_project_id(self.project_id, "closed")

    @property
    def has_milestone(self):
        rs = IssueMilestone.gets_by(issue_id=self.issue_id)
        return True if rs else None

    @property
    def milestone_id(self):
        rs = IssueMilestone.gets_by(issue_id=self.issue_id)
        return rs[0].milestone_id if rs else None

    @property
    def milestone_name(self):
        from vilya.models.milestone import Milestone
        m_id = self.milestone_id
        m = Milestone.get_by(m_id) if m_id else None
        return m.name if m else ''

    @property
    def milestone_percentage(self):
        from vilya.models.milestone import Milestone
        m_id = self.milestone_id
        m = Milestone.get_by(m_id) if m_id else None
        return m.percentage if m else 0

    def add_milestone(self, user, name=None, milestone_id=None):
        from vilya.models.milestone import Milestone
        target = self.target
        if name:
            ms = Milestone.get_by_project(target, name=name)
            if not ms:
                ms = Milestone.create_by_project(self.target, name, user)
        elif milestone_id:
            ms = Milestone.get_by(milestone_id)
        else:
            return None
        ims = IssueMilestone.get_by_issue(self)
        if ims:
            ims.milestone_id = ms.id
            ims.save()
        else:
            ims = IssueMilestone.create_by_issue(self, ms, user)

    def remove_milestone(self):
        ims = IssueMilestone.get_by_issue(self)
        if ims:
            ims.delete()

    @classmethod
    def get_multi_by(cls, *a, **kw):
        """ A wrapper to get project issues """
        # args
        issue_ids = kw.get('issue_ids')
        project = kw.get('project')
        creator = kw.get('creator')
        assignee = kw.get('assignee')
        state = kw.get('state')
        start = kw.get('start')
        limit = kw.get('limit')
        milestone = kw.get('milestone')
        tags = kw.get('tags')
        order = kw.get('order')
        ids = None

        # get ids
        issue_ids = cls._get_ids_by_project_id(
            project.id, order=order,
            state=state) if not issue_ids else issue_ids
        if milestone:
            ids = set(issue_ids) & set(milestone.issue_ids)
        if tags:
            ids = set(issue_ids) if not ids else ids
            for tag in tags:
                ids = ids & set(tag.project_issue_ids)
        if ids is not None:
            issue_ids = filter(lambda x: x in ids, issue_ids)
        issues = Issue.get_cached_issues(issue_ids)

        # filter
        if assignee:
            issues = filter(lambda x: x.assignee_id == assignee.name, issues)
        if creator:
            issues = filter(lambda x: x.creator_id == creator.name, issues)
        return dict(issues=issues[start:start + limit], total=len(issues))
