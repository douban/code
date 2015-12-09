# coding: utf-8
from __future__ import absolute_import
import requests

from vilya.libs.store import IntegrityError, store
from vilya.libs.props import PropsMixin, PropsItem
from vilya.libs.text import trunc_utf8
from vilya.models.consts import TEAM_MEMBER, TEAM_OWNER, UPLOAD_URL
from vilya.models.ticket import Ticket
from vilya.models.tag import TagMixin, TAG_TYPE_TEAM_ISSUE
from vilya.models.team_project import TeamProject
from vilya.models.nteam import TeamProjectRelationship, TeamUserRelationship


class Team(PropsMixin, TagMixin):

    def __init__(self, id, uid, name, description, created_at):
        self.id = id
        self.uid = uid
        self.name = name
        self.description = description
        self.created_at = created_at

    def get_uuid(self):
        return "/team/%s" % self.id

    uuid = property(get_uuid)

    profile = PropsItem("profile", {})
    weekly = PropsItem("weekly")

    def __repr__(self):
        return '<Team %s, %s>' % (self.id, self.uid)

    def __str__(self):
        return self.name

    def profile_url(self, pro_key='origin',
                    default='/static/img/team_default_profile.jpg'):
        if not self.profile:
            return default
        elif self.profile.get('origin') and not self.profile.get('icon'):
            # FIXME: 这段逻辑是为了让托管在c.dapps.douban.com的团队图片切换到p上面.
            # 一段时间后就可以删掉了
            return self.gen_profile_icon()
        else:
            return self.profile.get(pro_key, default)

    def gen_profile_icon(self):
        profile = self.profile
        picture_url = self.profile.get('origin')
        if 'c.dapps.douban.com' in picture_url:
            dirname = picture_url.rsplit('/', 1)[0]
            profile['icon'] = '{0}/i-96x96.jpg'.format(dirname)
        else:
            hash_png = picture_url.rsplit('/', 1)[1]
            rsize_url = '{0}/r/{1}?w=100&h=100'.format(UPLOAD_URL, hash_png)
            r = requests.get(rsize_url)
            r.raise_for_status()
            profile['icon'] = r.text
        self.profile = profile
        return profile['icon']

    def profile_icon(self):
        return self.profile_url('icon', '/static/img/logo.svg')

    @property
    def short_description(self):
        return trunc_utf8(self.description, 80)

    @property
    def url(self):
        return '/teams/%s/' % self.uid

    @property
    def tag_type(self):
        return TAG_TYPE_TEAM_ISSUE

    @property
    def doc_project(self):
        team_projects = TeamProject.gets_by(team_id=self.id)
        if not team_projects:
            return None
        team_project = team_projects[0]
        return team_project.project

    def as_dict(self):
        d = {}
        d['name'] = self.name
        d['description'] = self.description
        d['uid'] = self.uid
        d['created_at'] = self.created_at.strftime('%Y-%m-%dT%H:%M:%S')
        return d

    def delete(self):
        TeamProjectRelationship.deletes(team_id=self.id)
        TeamUserRelationship.deletes(team_id=self.id)
        del self.profile
        store.execute("delete from team where team_id=%s", (self.uid,))
        store.commit()

    @property
    def n_projects(self):
        return TeamProjectRelationship.count(team_id=self.id)

    @property
    def projects(self):
        from vilya.models.project import CodeDoubanProject
        return filter(None,
                      [CodeDoubanProject.get(_) for _ in self.project_ids])

    def is_project(self, project_id):
        r = TeamProjectRelationship.get(team_id=self.id, project_id=project_id)
        return True if r else False

    @property
    def project_ids(self):
        rs = TeamProjectRelationship.gets(team_id=self.id)
        return [r.project_id for r in rs]

    @property
    def n_tickets(self):
        return Ticket.get_count_by_team_id(self.id)

    def is_admin(self, user_id):
        return self.is_owner(user_id)

    def is_owner(self, user_id):
        r = TeamUserRelationship.get(team_id=self.id, user_id=user_id)
        return r and r.is_owner or False

    def is_member(self, user_id):
        r = TeamUserRelationship.get(team_id=self.id, user_id=user_id)
        return True if r else False

    def is_viewer(self, user_id):
        return True

    def had_joined(self, user_id):
        r = TeamUserRelationship.get(team_id=self.id, user_id=user_id)
        return r or False

    @property
    def owner_ids(self):
        rs = TeamUserRelationship.gets(team_id=self.id, identity=TEAM_OWNER)
        return [r.user_id for r in rs]

    @property
    def member_ids(self):
        rs = TeamUserRelationship.gets(team_id=self.id, identity=TEAM_MEMBER)
        return [r.user_id for r in rs]

    @property
    def user_ids(self):
        rs = TeamUserRelationship.gets(team_id=self.id)
        return [r.user_id for r in rs]

    @property
    def users(self):
        from vilya.models.user import User
        return [User(u) for u in self.user_ids]

    @property
    def all_members(self):
        # deprecated
        # used in mikoto
        return self.user_ids

    @property
    def n_owners(self):
        return TeamUserRelationship.count(team_id=self.id, identity=TEAM_OWNER)

    # TODO: rename to n_users
    @property
    def n_members(self):
        return TeamUserRelationship.count(team_id=self.id)

    @property
    def n_users(self):
        return TeamUserRelationship.count(team_id=self.id)

    @classmethod
    def get_by_user_id(cls, user_id):
        rls = TeamUserRelationship.gets(user_id=user_id)
        teams = [cls.get(rl.team_id) for rl in rls]
        return [(team.uid, team.name) for team in teams if team]

    @classmethod
    def gets_by_project_id(cls, project_id):
        return [cls.get(tpr.team_id)
                for tpr in TeamProjectRelationship.gets(project_id=project_id)]

    @classmethod
    def get_by_uid(cls, uid, ignore_case=True):
        # dirty hack
        if uid == 'fair':
            from vilya.models.fair import FairTeam
            return FairTeam()

        team_query = 'lower(`team_id`)' if ignore_case else 'team_id'

        rs = store.execute('select id, team_id, name, description, created_at '
                           'from team where {0}=%s'.format(team_query), (uid,))
        return rs and cls(*rs[0]) or None

    @classmethod
    def gets(cls):
        rs = store.execute('select id, team_id, name, description, created_at '
                           'from team order by id')
        return [cls(*r) for r in rs]

    @classmethod
    def gets_by_page(cls, start=0, limit=6):
        rs = store.execute('select id, team_id, name, description, created_at '
                           'from team order by id limit %s, %s',
                           (start, limit))
        return [cls(*r) for r in rs]

    @classmethod
    def get_all_team_uids(cls):
        rs = store.execute('select team_id from team order by id')
        return [r for r, in rs]

    @classmethod
    def get(cls, id):
        # dirty hack
        if id == 0:
            from vilya.models.fair import FairTeam
            return FairTeam()

        sets = store.execute('select id, team_id, name, '
                             'description, created_at '
                             'from team where id=%s', (id,))
        return sets and cls(*sets[0]) or None

    @classmethod
    def add(cls, uid, name, description):
        try:
            id = store.execute('insert into team '
                               '(team_id, name, description) '
                               'values(%s, %s, %s)',
                               (uid, name, description))
            store.commit()
        except IntegrityError:
            return None
        return cls.get(id)

    def update(self, uid, name, description):
        store.execute('update team set team_id=%s, name=%s, description=%s '
                      'where id=%s', (uid, name, description, int(self.id)))
        store.commit()

    def add_project(self, project):
        r = TeamProjectRelationship.get(team_id=self.id,
                                        project_id=project.id)
        if not r:
            TeamProjectRelationship.create(team_id=self.id,
                                           project_id=project.id)
            return True

    def remove_project(self, project):
        r = TeamProjectRelationship.get(team_id=self.id,
                                        project_id=project.id)
        if r:
            r.delete()
            return True

    def create_group(self, **kw):
        from vilya.models.team_group import TeamGroup
        kw['team_id'] = self.id
        t = TeamGroup.create(**kw)
        return t

    @property
    def groups(self):
        from vilya.models.team_group import TeamGroup
        return TeamGroup.gets(team_id=self.id)

    def add_user(self, user, identity):
        r = TeamUserRelationship.get(team_id=self.id,
                                     user_id=user.name)
        if not r:
            TeamUserRelationship.create(team_id=self.id,
                                        user_id=user.name,
                                        identity=identity)
            return True

    def remove_user(self, user):
        r = TeamUserRelationship.get(team_id=self.id,
                                     user_id=user.name)
        if r:
            r.delete()
            return True

    def add_owner(self, username):
        r = TeamUserRelationship.get(team_id=self.id,
                                     user_id=username)
        if not r:
            r = TeamUserRelationship.create(team_id=self.id,
                                            user_id=username,
                                            identity=TEAM_OWNER)
            return True
        if r.identity != TEAM_OWNER:
            r.identity = TEAM_OWNER
            r.save()
        return True

    def remove_owner(self, username):
        r = TeamUserRelationship.get(team_id=self.id,
                                     user_id=username)
        if r:
            if r.identity != TEAM_OWNER:
                return False
            r.delete()
        return True

    def add_member(self, username):
        r = TeamUserRelationship.get(team_id=self.id,
                                     user_id=username)
        if not r:
            r = TeamUserRelationship.create(team_id=self.id,
                                            user_id=username,
                                            identity=TEAM_MEMBER)
            return True
        if r.identity != TEAM_MEMBER:
            r.identity = TEAM_MEMBER
            r.save()
        return True

    def remove_member(self, username):
        r = TeamUserRelationship.get(team_id=self.id,
                                     user_id=username)
        if r:
            if r.identity != TEAM_MEMBER:
                return False
            r.delete()
        return True
