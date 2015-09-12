# -*- coding: utf-8 -*-
from vilya.libs.store import OrzField, OrzBase
from vilya.models.project import CodeDoubanProject


class TeamProject(OrzBase):
    __orz_table__ = "team_projects"
    team_id = OrzField(as_key=True)
    project_id = OrzField()
    created_at = OrzField(default='null')

    @property
    def project(self):
        return CodeDoubanProject.get(self.project_id)
