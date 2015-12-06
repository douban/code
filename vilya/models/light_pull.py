# -*- coding: utf-8 -*-
from __future__ import absolute_import

from vilya.libs.store import store
from vilya.libs.mlock import MLock
from vilya.models.project import CodeDoubanProject
from vilya.models.ticket import Ticket
from vilya.models.utils.decorators import cached_property


class LightPull(object):
    """ Light weight pull request """

    def __init__(self, id, from_proj_id, from_branch,
                 to_proj_id, to_branch, merged, ticket_id):
        self.id = id
        self.from_proj_id = from_proj_id
        self.from_branch = from_branch
        self.to_proj_id = to_proj_id
        self.to_branch = to_branch
        self.merged = merged
        self.ticket_id = ticket_id

    @cached_property
    def from_proj(self):
        return CodeDoubanProject.get(self.from_proj_id)

    @cached_property
    def to_proj(self):
        return CodeDoubanProject.get(self.to_proj_id)

    @cached_property
    def mlock(self):
        return MLock.merge_pull(proj_id=self.to_proj_id)

    def release_mlock(self):
        self.mlock.release()

    @classmethod
    def get_by_repo_and_pull(cls, project_name, pull_number):
        project = CodeDoubanProject.get_by_name(project_name)
        ticket = Ticket.get_by_projectid_and_ticketnumber(project.id,
                                                          pull_number)

        def get_id_by_repo_and_pull(proj_id, ticket_id):
            rs = store.execute("select id from pullreq "
                               "where to_project=%s and ticket_id=%s",
                               (proj_id, ticket_id))
            return rs[0][0] if rs else ''

        id_ = get_id_by_repo_and_pull(project.id, ticket.ticket_id)
        return cls.get(id_)

    @classmethod
    def get(cls, id):
        rs = store.execute("select id, from_project, from_branch, "
                           "to_project, to_branch, merged, ticket_id "
                           "from pullreq "
                           "where id=%s",
                           (id,))
        return rs and cls(*rs[0])
