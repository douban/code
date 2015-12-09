# -*- coding: utf-8 -*-

from vilya.models.actions.base import Action, ActionScope


# TODO
#            url='/hub/team/%s/' % self._team_uid,
#            team_name=self._team_name,
#            actor=self._sender,
#            date=datetime.now(),
#            identity=self._identity,
#            type='team_add_member',
class TeamAddMember(Action):
    def __init__(self, sender, date, to_user, team_name, identity, url):
        super(TeamAddMember, self).__init__(sender, date)
        self.to_user = to_user
        self.team_name = team_name
        self.identity = identity
        self.url = url  # TODO url, uid

        self._target = to_user

    @property
    def type(self):
        return 'team_add_member'

    @property
    def scope(self):
        return ActionScope.user

    @property
    def target(self):
        return self._target

    @property
    def entry_title(self):
        return 'About you'

migrate_team_add_member = {
    'sender': 'actor',
    'to_user': ('', lambda x: 'you'),
    'target': ('', lambda x: 'you'),  # don't know who is the target, but 'you'
    'scope': ('', lambda x: 'user'),  # only user has
    'entry_title': ('', lambda x: 'About you'),
}
