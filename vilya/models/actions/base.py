# -*- coding: utf-8 -*-

from vilya.libs.text import trunc_utf8


class ActionScope(object):
    project = 'project'
    team = 'team'
    fair = 'fair'
    user = 'user'

    all_scopes = ('project',
                  'team',
                  'fair',
                  'user',
                  )

    @classmethod
    def getScope(cls, target_type):
        if target_type in cls.all_scopes:
            return target_type
        else:
            return None


class Action(object):
    def __init__(self, sender, date):
        self.sender = sender
        self.date = date
        # TODO: action uid, consider 'mark as read'

    @property
    def type(self):
        ''' action type, e.g. issue_comment '''
        return self.__class__.__name__.lower()

    @property
    def scope(self):
        ''' ActionScope.xxx '''
        pass

    @property
    def target(self):
        ''' action belong to, e.g. project_name, team_name, user_name '''
        pass

    @property
    def entry_id(self):
        ''' e.g. issue_number, pull_number, commit_ref, '''
        # TODO: user scope的entry里就自己一条，应该拿uid来顶
        return ''

    @property
    def entry_title(self):
        ''' e.g. issue_title '''
        pass

    @property
    def notif_template(self):
        return self.type + '_notif'

    @property
    def feed_template(self):
        return self.type + '_feed'

    @classmethod
    def _truncate(cls, s, cnt=80):
        return trunc_utf8(s, cnt)

    def to_dict(self):
        import inspect
        dt = self.__dict__.copy()
        dt.update([(p, getattr(self, p))
                   for (p, v) in inspect.getmembers(self.__class__,
                   lambda v: isinstance(v, property))])
        dt = {k: dt[k] for k in dt if not k.startswith('_')}
        return dt
