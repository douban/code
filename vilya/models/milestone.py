# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division

from datetime import datetime

from vilya.libs.store import OrzField, store, IntegrityError, OrzBase

PROJECT_MILESTONE_TYPE = 1


class MTCounter(object):
    """Milestone Target Counter"""

    @classmethod
    def incr(cls, target_id, target_type, count=None):
        if count and count >= 0:
            sql = (
                "insert into milestone_counters "
                "(target_id, target_type, counter) "
                "values (%s, %s, LAST_INSERT_ID(%s)) "
                "on duplicate key update counter = LAST_INSERT_ID(%s)")
            id = store.execute(sql, (target_id, target_type, count, count))
        else:
            sql = (
                "insert into milestone_counters "
                "(target_id, target_type, counter) "
                "values (%s, %s, LAST_INSERT_ID(%s)) on duplicate key "
                "update counter = LAST_INSERT_ID(counter + 1)")
            id = store.execute(sql, (target_id, target_type, 1))
        store.commit()
        return id


class Milestone(OrzBase):
    __orz_table__ = "milestones"
    name = OrzField(as_key=OrzField.KeyType.DESC)
    creator_id = OrzField()
    target_id = OrzField(as_key=OrzField.KeyType.DESC)
    target_type = OrzField(as_key=OrzField.KeyType.DESC)
    target_number = OrzField(as_key=OrzField.KeyType.DESC)
    created_at = OrzField(default='null')

    class OrzMeta:
        id2str = True

    # FIXME: ugly wrapper
    @classmethod
    def create_by_project(cls, project, name, user):
        target_number = MTCounter.incr(project.id, PROJECT_MILESTONE_TYPE)
        try:
            ms = cls.create(name=name,
                            target_id=project.id,
                            target_type=PROJECT_MILESTONE_TYPE,
                            target_number=target_number,
                            creator_id=user.name,
                            created_at=datetime.now())
        except IntegrityError:
            store.rollback()
            rs = cls.gets_by(target_id=project.id,
                             target_type=PROJECT_MILESTONE_TYPE,
                             target_number=target_number)
            ms = rs[0]
            ms.name = name
            ms.save()
        return ms

    # FIXME: ugly wrapper
    @classmethod
    def gets_by_project(cls, project, number=None, name=None):
        if name:
            rs = cls.gets_by(name=name, target_id=project.id,
                             target_type=PROJECT_MILESTONE_TYPE)
        elif number:
            rs = cls.gets_by(target_id=project.id,
                             target_type=PROJECT_MILESTONE_TYPE,
                             target_number=number)
        else:
            rs = cls.gets_by(target_id=project.id,
                             target_type=PROJECT_MILESTONE_TYPE)
        return rs

    # FIXME: ugly wrapper
    @classmethod
    def get_by_project(cls, project, number=None, name=None):
        rs = cls.gets_by_project(project, number=number, name=name)
        return rs[0] if rs else None

    @property
    def tasks(self):
        from vilya.models.milestone_task import MilestoneTask
        return MilestoneTask(self).get_multi()

    @property
    def issue_ids(self):
        from vilya.models.milestone_task import MilestoneTask
        # TODO: check milestone type
        ms = MilestoneTask(self).get_multi()
        # TODO: orz return int
        return [int(m.issue_id) for m in ms]

    @property
    def open_tasks(self):
        from vilya.models.milestone_task import MilestoneTask
        return MilestoneTask(self).get_multi(state="open")

    @property
    def closed_tasks(self):
        from vilya.models.milestone_task import MilestoneTask
        return MilestoneTask(self).get_multi(state="closed")

    @property
    def percentage(self):
        closed_count = self.closed_task_count
        count = self.task_count
        return closed_count / count * 100 if count else 0

    @property
    def percentage_number(self):
        number = str(self.percentage)
        number = number.split('.')[0]
        return number

    @property
    def open_task_count(self):
        return len(self.open_tasks)

    @property
    def closed_task_count(self):
        return len(self.closed_tasks)

    @property
    def task_count(self):
        return len(self.tasks)
