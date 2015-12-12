# -*- coding: utf-8 -*-
from __future__ import absolute_import
from datetime import datetime
import operator

from vilya.libs.store import store, mc, cache, mc_gets, bdb
from vilya.models.tag import Tag, TagName
from vilya.models.issue_vote import Upvote
from vilya.models.issue_participant import IssueParticipant
from vilya.models.issue_comment import IssueComment

MC_KEY_ISSUE = 'issue:v3:%s'
MC_KEY_ISSUES_DATA_BY_TARGET = 'issues_data:v3:type:%s:target_id:%s'
MC_KEY_ISSUES_IDS_BY_CREATOR_ID = 'issue_ids_by_creator_id:v3:%s'
MC_KEY_ISSUES_IDS_BY_ASSIGNEE_ID = 'issues_ids_by_assignee_id:v3:%s'
MC_KEY_USER_ISSUE_IDS_BY_CREATOR_ID = 'user_issue:v3:%s'
BDB_ISSUE_DESCRIPTION_KEY = 'issue_description:%s'
ISSUE_DATA_FIELDS = dict(issue_id=0, closer_id=1, updated_at=2, rank_score=3)


def filter_issue_ids_by_score(ids, order):
    if order == 'hot':
        index = ISSUE_DATA_FIELDS['rank_score']
        ids = [info for info
               in sorted(ids, key=operator.itemgetter(index), reverse=True)]
    else:
        index = ISSUE_DATA_FIELDS['updated_at']
        ids = [info for info
               in sorted(ids, key=operator.itemgetter(index), reverse=True)]
    return ids


def filter_issue_ids_by_state(ids, state):
    index = ISSUE_DATA_FIELDS['closer_id']
    if state:
        if state == 'open':
            ids = [info for info in ids if not info[index]]
        elif state == 'closed':
            ids = [info for info in ids if info[index]]
    return ids


class Issue(object):
    target_type = 'default'
    tag_type = 0  # not exists type
    provided_features = []  # Interface

    def __init__(self, id, title,
                 creator, assignee=None, closer=None,
                 created_at=None, updated_at=None, closed_at=None,
                 type='default', target_id=0):
        self.id = id
        self.issue_id = id
        self.title = title
        bdb_description = bdb.get(BDB_ISSUE_DESCRIPTION_KEY % id)
        self.description = bdb_description
        self.creator_id = creator
        self.assignee_id = assignee
        self.closer_id = closer
        self.created_at = created_at
        self.updated_at = updated_at
        self.closed_at = closed_at
        self.type = type
        self.number = 0
        self.target_id = target_id

    def __repr__(self):
        return '<%s(%s)>' % (self.__class__.__name__, self.id)

    @property
    def url(self):
        raise NotImplementedError('Subclasses should implement this!')

    @property
    def target(self):
        raise NotImplementedError('Subclasses should implement this!')

    def provide(self, name):
        '''检查是否提供某功能，即是否提供某接口'''
        return name in self.provided_features

    @property
    def state(self):
        if self.closer_id:
            return 'closed'

        return 'open'

    @property
    def is_closed(self):
        return self.state == 'closed'

    @property
    def creator(self):
        if self.creator_id:
            from vilya.models.user import User
            return User(self.creator_id)
        return None

    @property
    def closer(self):
        if self.closer_id:
            from vilya.models.user import User
            return User(self.closer_id)
        return None

    @property
    def assignee(self):
        if self.assignee_id:
            from vilya.models.user import User
            return User(self.assignee_id)
        return None

    def clear_cache(self):
        mc.delete(MC_KEY_ISSUE % self.issue_id)

    def update(self, title, description):
        store.execute("update issues "
                      "set title=%s, updated_at=null "
                      "where id=%s", (title, self.issue_id))
        store.commit()
        bdb.set(BDB_ISSUE_DESCRIPTION_KEY % self.issue_id, description)
        self.clear_cache()
        mc.delete(MC_KEY_ISSUES_DATA_BY_TARGET % (self.type, self.target_id))

    def close(self, user_id):
        store.execute("update issues "
                      "set closer_id=%s, closed_at=null "
                      "where id=%s", (user_id, self.issue_id))
        store.commit()
        self.clear_cache()
        mc.delete(MC_KEY_ISSUES_IDS_BY_CREATOR_ID % self.creator_id)
        mc.delete(MC_KEY_ISSUES_DATA_BY_TARGET % (self.type, self.target_id))
        self.closer_id = user_id

    def open(self):
        store.execute("update issues "
                      "set closer_id=null, closed_at=null "
                      "where id=%s", (self.issue_id,))
        store.commit()
        self.clear_cache()
        mc.delete(MC_KEY_ISSUES_IDS_BY_CREATOR_ID % self.creator_id)
        mc.delete(MC_KEY_ISSUES_DATA_BY_TARGET % (self.type, self.target_id))
        self.closer_id = None

    def add_tag(self, tag, type, target_id, author=None):
        author_id = author if author else self.creator_id
        # create tag if not exists
        tag_name = TagName.get_by_name_and_target_id(tag, type, target_id)
        if not tag_name:
            tag_name = TagName.add(tag, author_id, type, target_id)
        if not tag_name:
            return
        # add tag to issue if not already be added
        issue_tag = Tag.get_by_type_id_and_tag_id(
            type, self.issue_id, tag_name.id)
        if issue_tag:
            return
        Tag.add_to_issue(
            tag_name.id, type, self.issue_id, author_id, target_id)

    def add_tags(self, tags, target_id, author=None):
        for tag in tags:
            self.add_tag(tag, self.tag_type, target_id, author)

    def remove_tag(self, tag, type, target_id):
        # check if tag exists
        tag_name = TagName.get_by_name_and_target_id(tag, type, target_id)
        if not tag_name:
            return
        # delete tag relationship if exists
        issue_tag = Tag.get_by_type_id_and_tag_id(
            type, self.issue_id, tag_name.id)
        if issue_tag:
            issue_tag.delete()

    def remove_tags(self, tags, target_id):
        for tag in tags:
            self.remove_tag(tag, self.tag_type, target_id)

    def upvote_by_user(self, user_id):
        if user_id and (user_id != self.creator_id) and not self.is_closed:
            vote = Upvote.add(self.issue_id, user_id)
            if vote:
                self.update_rank_score()
        return self.vote_count

    def cancel_upvote_by_user(self, user_id):
        ok = Upvote.delete(self.issue_id, user_id)
        if ok:
            self.update_rank_score()
        return self.vote_count

    def has_user_voted(self, user_id):
        if user_id:
            vote = Upvote.get_by_issue_id_and_user_id(self.issue_id, user_id)
            return True if vote else False
        return False

    @property
    def vote_count(self):
        return Upvote.count_by_issue_id(self.issue_id)

    @property
    def comments(self):
        return IssueComment.gets_by_issue_id(self.issue_id)

    @property
    def comment_count(self):
        return IssueComment.count_by_issue_id(self.issue_id)

    def add_comment(self, content, user):
        res = IssueComment.add(self.issue_id, content, user)
        self.update_rank_score()
        return res

    def update_rank_score(self):
        vote_count = self.vote_count
        comment_count = self.comment_count
        time_delta = (datetime.now() - datetime(2011, 1, 1)).total_seconds()
        divider = (datetime(2013, 7, 8) - datetime(2011, 1, 1)).total_seconds()
        time_factor = time_delta / divider * 5
        score = (vote_count * 0.5 + comment_count) * time_factor
        store.execute(
            "update issues "
            "set rank_score=%s , updated_at=updated_at "  # 防止字段更新
            "where id=%s ",
            (score, self.issue_id))
        store.commit()
        mc.delete(MC_KEY_ISSUES_DATA_BY_TARGET % (self.type, self.target_id))
        return score

    def add_participants(self, user_ids):
        for user_id in user_ids:
            self.add_participant(user_id)

    def add_participant(self, user_id):
        p = IssueParticipant.get_by_issue_id_and_user_id(self.issue_id,
                                                         user_id)
        if not p:
            IssueParticipant.add(self.issue_id, user_id)

    def delete_participant(self, user_id):
        p = IssueParticipant.get_by_issue_id_and_user_id(self.issue_id,
                                                         user_id)
        if p:
            p.delete()

    def has_participated(self, user_id):
        return bool(IssueParticipant.get_by_issue_id_and_user_id(
            self.issue_id, user_id))

    @property
    def participants(self):
        return IssueParticipant.gets_by_issue_id(self.issue_id)

    def assign(self, user_id):
        old_id = self.assignee_id
        store.execute("update issues "
                      "set assignee_id=%s "
                      "where id=%s", (user_id, self.issue_id))
        store.commit()
        self.clear_cache()
        mc.delete(MC_KEY_ISSUES_IDS_BY_ASSIGNEE_ID % old_id)
        mc.delete(MC_KEY_ISSUES_IDS_BY_ASSIGNEE_ID % user_id)

    @classmethod
    def add(cls, title, description, creator, assignee=None, closer=None,
            created_at=None, updated_at=None, closed_at=None,
            type='default', target_id=0):
        time = datetime.now()
        issue_id = store.execute(
            'insert into issues (title, creator_id, '
            'assignee_id, closer_id, created_at, updated_at, type, target_id) '
            'values (%s, %s, %s, %s, NULL, NULL, %s, %s)',
            (title, creator, assignee, closer, type, target_id))
        store.commit()
        mc.delete(MC_KEY_ISSUE % issue_id)
        mc.delete(MC_KEY_ISSUES_IDS_BY_CREATOR_ID % creator)
        mc.delete(MC_KEY_ISSUES_IDS_BY_ASSIGNEE_ID % assignee)
        mc.delete(MC_KEY_ISSUES_DATA_BY_TARGET % (type, target_id))
        bdb.set(BDB_ISSUE_DESCRIPTION_KEY % issue_id, description)
        issue = cls(issue_id, title, creator, assignee, closer, time, time)
        issue.add_participant(creator)
        return issue

    def delete(self):
        store.execute('delete from issues where id=%s', (self.id,))
        store.commit()
        mc.delete(MC_KEY_ISSUE % self.id)
        mc.delete(MC_KEY_ISSUES_IDS_BY_CREATOR_ID % self.creator_id)
        mc.delete(MC_KEY_ISSUES_IDS_BY_ASSIGNEE_ID % self.assignee_id)
        mc.delete(MC_KEY_ISSUES_DATA_BY_TARGET % (type, self.target_id))
        bdb.set(BDB_ISSUE_DESCRIPTION_KEY % self.id, '')

    @classmethod
    def get(cls, id):
        rs = store.execute(
            "select id, title, creator_id, assignee_id, closer_id, "
            "created_at, updated_at, closed_at, type, target_id "
            "from issues where id=%s", (id,))
        return rs and cls(*rs[0]) or None

    @classmethod
    def get_by_issue_id(cls, id, state=None):
        issue = Issue.get(id)
        if not issue:
            return None

        if state and issue.state != state:
            return None

        return issue

    @classmethod
    @cache(MC_KEY_ISSUES_DATA_BY_TARGET % ('{cls.target_type}', '{target_id}'))
    def get_data_by_target(cls, target_id):
        rs = store.execute('select id, closer_id, updated_at, rank_score '
                           'from issues where type=%s and target_id=%s',
                           (cls.target_type, target_id))
        return rs

    @classmethod
    def gets_by_target(cls, target_id, state=None, order='',
                       limit=0, start=0):
        data = cls.get_data_by_target(target_id)
        data = filter_issue_ids_by_state(data, state)
        data = filter_issue_ids_by_score(data, order)
        ids = [issue_id for (issue_id, _, _, _) in data]
        if limit:
            ids = ids[start:start + limit]
        return Issue.get_cached_issues(ids)

    @classmethod
    def gets_by_creator_id(cls, id, state='open'):
        # FIXME 子类中的这个方法，参数非常不一致。需要尽快解决
        result = cls.get_ids_by_creator_id(id)
        if state == 'open':
            ids = [i for (i, closer_id) in result if not closer_id]
            return Issue.get_cached_issues(ids)
        else:
            ids = [i for (i, closer_id) in result if closer_id]
            return Issue.get_cached_issues(ids)

    @classmethod
    @cache(MC_KEY_ISSUES_IDS_BY_CREATOR_ID % '{id}')
    def get_ids_by_creator_id(cls, id):
        rs = store.execute("select id, closer_id "
                           "from issues "
                           "where creator_id = %s",
                           (id,))
        return rs

    @classmethod
    def gets_by_assignee_id(cls, id, state='open'):
        # FIXME 子类中的这个方法，参数非常不一致。需要尽快解决
        result = cls.get_ids_by_assignee_id(id)
        if state == 'open':
            ids = [i for (i, closer_id) in result if not closer_id]
            return Issue.get_cached_issues(ids)
        else:
            ids = [i for (i, closer_id) in result if closer_id]
            return Issue.get_cached_issues(ids)

    @classmethod
    def gets_by_participated_user(cls, user_id, state='open'):
        ps = IssueParticipant.gets_by_user_id(user_id)
        issue_ids = [p.issue_id for p in ps]
        issues = Issue.get_cached_issues(issue_ids)
        issues_with_state = [issue for issue in issues
                             if (state == 'open') is (not issue.closer_id)]
        return issues_with_state

    @classmethod
    @cache(MC_KEY_ISSUES_IDS_BY_ASSIGNEE_ID % '{id}')
    def get_ids_by_assignee_id(cls, id):
        rs = store.execute("select id, closer_id "
                           "from issues "
                           "where assignee_id = %s",
                           (id,))
        return rs

    @classmethod
    def gets_by_closer_id(cls, id):
        rs = store.execute("select id, title, "
                           "creator_id, assignee_id, closer_id, "
                           "created_at, updated_at, closed_at, type "
                           "from issues "
                           "where closer_id = %s ",
                           (id, ))
        return [cls(*r) for r in rs]

    @property
    def tags(self):
        return Tag.gets_by_issue_id(self.issue_id, self.tag_type)

    @staticmethod
    @cache(MC_KEY_ISSUE)
    def get_cached_issue(id):
        from vilya.models.issue_utils import ISSUE_TYPE_CLASS
        issue = Issue.get(id)
        if issue:
            subcls = ISSUE_TYPE_CLASS[issue.type]
            return subcls.get_by_issue_id(id)

    @staticmethod
    def get_cached_issues(ids):
        issues = mc_gets(MC_KEY_ISSUE, Issue.get_cached_issue, ids)
        return [i for i in issues if i]


def get_project_issues(issues):
    project_issues = []
    for issue in issues:
        project_issue = get_issue_by_id_and_state(issue.issue_id)
        if project_issue:
            project_issues.append(project_issue)
    return project_issues


# return project_issue or team_issue
def get_issue_by_id_and_state(id, state=None):
    issue = Issue.get_cached_issue(id)
    if not issue:
        return None

    if state and issue.state != state:
        return None

    return issue
