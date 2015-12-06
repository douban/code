# coding: utf-8

from datetime import datetime

from vilya.models.team import Team
from vilya.models.tag import TAG_TYPE_FAIR_ISSUE


FAIR_ID = 0


class FairTeam(Team):
    def __init__(self):
        self.id = FAIR_ID
        self.team_id = FAIR_ID
        self.uid = 'fair'
        self.name = 'fair'
        self.description = ''
        self.created_at = datetime(2013, 7, 19)

    def __repr__(self):
        return '<FairTeam>'

    def __str__(self):
        return self.name

    def get_uuid(self):
        return '/fair'

    @property
    def url(self):
        return '/fair/'

    @property
    def tag_type(self):
        return TAG_TYPE_FAIR_ISSUE

    def delete(self):
        # can not delete
        pass

    def is_admin(self, user_id):
        return user_id in ['xyb', 'testuser', 'qingfeng', 'huanghuang', 'xutao']  # noqa

    def is_creator(self, user_id):
        return self.is_admin(user_id)

    def is_viewer(self, user_id):
        return True

    def had_joined(self, user_id):
        # all companee can use fair
        return True


def get_fair():
    return Team.get(FAIR_ID)
