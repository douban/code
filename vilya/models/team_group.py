# -*- coding: utf-8 -*-
from vilya.libs.model import BaseModel, ModelField
from vilya.models.consts import (
    PERM_PULL, PERM_PUSH, PERM_ADMIN, PERM_MERGE, PERM_TEXT)


class TeamGroup(BaseModel):
    __orz_table__ = "team_groups"
    name = ModelField(as_key=ModelField.KeyType.DESC)
    team_id = ModelField(as_key=ModelField.KeyType.DESC)
    description = ModelField()
    permission = ModelField(as_key=ModelField.KeyType.DESC,
                            default=PERM_PULL)
    creator_id = ModelField()
    created_at = ModelField(auto_now_create=True)

    @property
    def permission_text(self):
        return PERM_TEXT.get(self.permission, 'pull')

    def add_user(self, **kw):
        kw['group_id'] = self.id
        return GroupUser.create(**kw)

    def add_project(self, **kw):
        kw['group_id'] = self.id
        return ProjectGroup.create(**kw)

    def remove_user(self, **kw):
        kw['group_id'] = self.id
        u = GroupUser.get(**kw)
        if u:
            u.delete()

    def remove_project(self, **kw):
        kw['group_id'] = self.id
        u = ProjectGroup.get(**kw)
        if u:
            u.delete()

    @property
    def url(self):
        return self.team.url + 'groups/%s/' % self.name

    @property
    def team(self):
        from vilya.models.team import Team
        return Team.get(self.team_id)

    @property
    def full_name(self):
        return "%s/%s" % (self.team.uid, self.name)

    @property
    def members(self):
        from vilya.models.user import User
        rs = GroupUser.gets(group_id=self.id)
        return [User(r.user_id) for r in rs]

    @property
    def projects(self):
        from vilya.models.project import CodeDoubanProject
        rs = ProjectGroup.gets(group_id=self.id)
        return filter(None, [CodeDoubanProject.get(r.project_id) for r in rs])

    def is_member(self, user_id):
        r = GroupUser.get(group_id=self.id, user_id=user_id)
        return True if r else False

    def to_dict(self):
        return dict(name=self.name,
                    team_id=self.team_id)

    @classmethod
    def translate_perm(cls, perm):
        r = PERM_PULL
        if perm == 'push':
            r = PERM_PUSH
        elif perm == 'merge':
            r = PERM_MERGE
        elif perm == 'admin':
            r = PERM_ADMIN
        return r


class GroupUser(BaseModel):
    __orz_table__ = "group_users"
    group_id = ModelField(as_key=ModelField.KeyType.DESC)
    user_id = ModelField(as_key=ModelField.KeyType.DESC)
    created_at = ModelField(auto_now_create=True)

    @property
    def group(self):
        return TeamGroup.get(id=self.group_id)

    @property
    def user(self):
        from vilya.models.user import User
        return User(self.user_id)

    def to_dict(self):
        return dict(group_name=self.group.name,
                    user_name=self.user_id)


class ProjectGroup(BaseModel):
    __orz_table__ = "projects_groups"
    project_id = ModelField(as_key=ModelField.KeyType.DESC)
    group_id = ModelField(as_key=ModelField.KeyType.DESC)
    created_at = ModelField(auto_now_create=True)

    @property
    def group(self):
        return TeamGroup.get(id=self.group_id)

    @property
    def project(self):
        from vilya.models.project import CodeDoubanProject
        return CodeDoubanProject.get(self.project_id)

    def to_dict(self):
        return dict(group_name=self.group.name,
                    project_name=self.project.name)
