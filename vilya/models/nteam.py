# -*- coding: utf-8 -*-
from vilya.libs.store import OrzField, OrzBase
from vilya.libs.model import BaseModel, ModelField
from vilya.libs.props import PropsMixin, PropsItem
from vilya.models.tag import TagMixin, TAG_TYPE_TEAM_ISSUE
from vilya.models.team_project import TeamProject
from vilya.models.consts import (
    TEAM_MEMBER, TEAM_OWNER)


# TODO: not used ~
class Team(OrzBase, PropsMixin, TagMixin):
    __orz_table__ = "team"
    team_id = OrzField(as_key=OrzField.KeyType.DESC)
    name = OrzField(as_key=OrzField.KeyType.DESC)
    description = OrzField(default='')
    created_at = OrzField(default='null')

    @property
    def uid(self):
        # TODO: change uid to name
        return self.team_id

    @property
    def title(self):
        return self.name

    def __repr__(self):
        return '<Team %s, %s>' % (self.id, self.uid)

    def __str__(self):
        return self.name

    def get_uuid(self):
        return "/team/%s" % self.id

    uuid = property(get_uuid)
    profile = PropsItem("profile", {})
    weekly = PropsItem("weekly")

    def profile_url(self):
        if not self.profile:
            return "/static/img/team_default_profile.jpg"
        else:
            return self.profile.get('origin')

    @property
    def tag_type(self):
        return TAG_TYPE_TEAM_ISSUE

    @property
    def url(self):
        return '/teams/%s/' % self.uid

    @property
    def doc_project(self):
        team_projects = TeamProject.gets_by(team_id=self.id)
        if not team_projects:
            return None
        team_project = team_projects[0]
        return team_project.project

    @property
    def members(self):
        pass

    @property
    def owners(self):
        pass

    @property
    def projects(self):
        from vilya.models.project import CodeDoubanProject
        return filter(None, [CodeDoubanProject.get(_)
                             for _ in self.project_ids])

    def as_dict(self):
        d = {}
        d['name'] = self.name
        d['description'] = self.description
        d['uid'] = self.uid
        d['created_at'] = self.created_at.strftime('%Y-%m-%dT%H:%M:%S')
        return d


class TeamUserRelationship(BaseModel):
    __orz_table__ = "team_user_relationship"
    team_id = ModelField(as_key=ModelField.KeyType.DESC)
    user_id = ModelField(as_key=ModelField.KeyType.DESC)
    identity = ModelField(as_key=ModelField.KeyType.DESC)
    created_at = ModelField(auto_now_create=True)

    class OrzMeta:
        id2str = True

    def __repr__(self):
        return '<TeamUserRelationship %s, %s, %s>' % (self.id,
                                                      self.team_id,
                                                      self.user_id)

    @property
    def is_owner(self):
        return self.identity == TEAM_OWNER

    @property
    def is_member(self):
        return self.identity == TEAM_MEMBER


class TeamProjectRelationship(BaseModel):
    __orz_table__ = "team_project_relationship"
    team_id = ModelField(as_key=ModelField.KeyType.DESC)
    project_id = ModelField(as_key=ModelField.KeyType.DESC)
    created_at = ModelField(auto_now_create=True)

    class OrzMeta:
        id2str = True

    def __repr__(self):
        return '<TeamProjectRelationship %s, %s, %s>' % (self.id,
                                                         self.team_id,
                                                         self.project_id)
