# -*- coding: utf-8 -*-

from __future__ import absolute_import
from vilya.models.project_issue import ProjectIssue
from vilya.models.issue_milestone import IssueMilestone


class MilestoneTask(object):

    def __init__(self, milestone):
        self.milestone = milestone

    def get_multi(self, state=None):
        # FIXME: cache
        milestone = self.milestone
        if state == 'open':
            return self._get_open_multi()
        if state == 'closed':
            return self._get_closed_multi()
        return IssueMilestone.gets_by(milestone_id=milestone.id)

    def _get_open_multi(self):
        milestone = self.milestone
        tasks = []
        rs = IssueMilestone.gets_by(milestone_id=milestone.id)
        for r in rs:
            issue = ProjectIssue.get_by_issue_id(r.issue_id)
            if not issue:
                continue
            if not issue.closer_id:
                tasks.append(r)
        return tasks

    def _get_closed_multi(self):
        milestone = self.milestone
        tasks = []
        rs = IssueMilestone.gets_by(milestone_id=milestone.id)
        for r in rs:
            issue = ProjectIssue.get_by_issue_id(r.issue_id)
            if not issue:
                continue
            if issue.closer_id:
                tasks.append(r)
        return tasks
