# -*- coding: utf-8 -*-

from vilya.models.actions.base import Action, ActionScope


# TODO
#                author=recommend.from_user,
#                from_user=recommend.from_user,
#                to_user=recommend.to_user,
#                content=recommend.content,
#                type='recommend',
#                date=recommend.created,
#                url=('%s/people/%s/praises' % (DOMAIN, recommend.to_user))
class Recommend(Action):
    def __init__(self, sender, date, recommend, url):
        super(Recommend, self).__init__(sender, date)  # sender <- from_user
        self.to_user = recommend.to_user
        self.content = Recommend._truncate(recommend.content)
        self.url = url  # TODO url, DOMAIN

    @property
    def scope(self):
        return ActionScope.user

    @property
    def target(self):
        return self.to_user

    @property
    def entry_title(self):
        return 'About you'

migrate_recommend = {
    'sender': 'author',
    'target': 'to_user',
    'scope': ('', lambda x: 'user'),  # only user has
    'entry_title': ('', lambda x: 'About you'),
}
