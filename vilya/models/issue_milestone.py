# -*- coding: utf-8 -*-
from __future__ import absolute_import
from datetime import datetime

from vilya.libs.store import OrzField, OrzBase
from vilya.models.milestone import Milestone


class IssueMilestone(OrzBase):
    __orz_table__ = "issue_milestones"
    issue_id = OrzField(as_key=True)
    milestone_id = OrzField(as_key=True)
    creator_id = OrzField()
    created_at = OrzField(default='null')

    class OrzMeta:
        id2str = True

    @property
    def milestone(self):
        return Milestone.get_by(self.milestone_id)

    @classmethod
    def get_by_issue(cls, issue):
        rs = cls.gets_by(issue_id=issue.issue_id)
        r = rs[0] if rs else None
        return r

    @classmethod
    def create_by_issue(cls, issue, milestone, user):
        ims = cls.create(issue_id=issue.issue_id, milestone_id=milestone.id,
                         creator_id=user.name, created_at=datetime.now())
        return ims
