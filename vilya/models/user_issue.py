# -*- coding: utf-8 -*-

from __future__ import absolute_import


class UserIssue(object):

    def __init__(self, username):
        self.name = username

    # FIXME: including open & closed
    @classmethod
    def gets_by_creator_id(cls, user_id, state=None):
        from vilya.models.issue import Issue
        return Issue.gets_by_creator_id(user_id, state)

    # FIXME: including open & closed
    @classmethod
    def gets_by_assignee_id(cls, user_id, state=None):
        from vilya.models.issue import Issue
        return Issue.gets_by_assignee_id(user_id, state)

    @classmethod
    def get_participated_issues(cls, user_id, state=None):
        from vilya.models.issue import Issue
        issues_created = cls.gets_by_creator_id(user_id, state)
        issues = [issue for issue in Issue.gets_by_participated_user(user_id,
                                                                     state)
                  if issue not in issues_created]
        return issues
