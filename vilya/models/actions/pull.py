# -*- coding: utf-8 -*-

from vilya.models.actions.base import Action, ActionScope


# TODO
#            'date': self.now(),
#            'url': pullreq_url,
#            'description': description,
#            'from_proj': from_proj_str,
#            'to_proj': to_proj_str,
#            'commiter': commiter,
#            'owner': owner,
#            'title': title,
#            'status': status,
#            'type': 'pull_request'
class Pull(Action):

    # FIXME: 把计算都放到 相应的 models 里去（ticket/pr）

    def __init__(self, sender, date, pullreq, ticket, owner, state, url):
        super(Pull, self).__init__(sender, date)  # sender <- commiter
        self.to_proj = pullreq.to_proj_str
        self.from_proj = pullreq.from_proj_str
        self.owner = owner
        self.title = ticket.title
        self.ticket = ticket.ticket_id
        self.state = state  # <- status
        self.content = Pull._truncate(ticket.description)  # <- description
        self.url = url

        self._target = pullreq.to_proj.name

    @property
    def type(self):
        return 'pull_request'

    @property
    def scope(self):
        return ActionScope.project

    @property
    def target(self):
        return self._target

    @property
    def entry_id(self):
        return self.ticket

    @property
    def entry_title(self):
        return '#%d %s' % (self.ticket, self.title)


def _migrate_ticket_id(url):
    ''' hack from url '''
    if url.split('/')[3].isdigit():
        return int(url.split('/')[3])
    elif url.split('/')[4].isdigit():
        return int(url.split('/')[4])
    return ''

migrate_pull_request = {
    'sender': 'commiter',
    'content': 'description',
    'state': 'status',
    'target': ('to_proj', lambda x: x.split(':')[0]),
    'scope': ('', lambda x: 'project'),  # only projects has
    'ticket': ['url', _migrate_ticket_id],
    'entry_id': ['url', _migrate_ticket_id],  # force update
    'entry_title': 'title',
}
