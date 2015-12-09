# -*- coding: utf-8 -*-

from vilya.models.actions.base import Action, ActionScope


# TODO
#            date=self.now(),
#            url=url,
#            ticket=ticket_id,
#            proj="%s:%s" % (pullreq.to_proj, pullreq.to_branch),
#            receiver=ticket_author,
#            author=sender,
#            text=content,
#            type='code_review',
class PullComment(Action):
    def __init__(self, sender, date, pullreq, ticket, content, url):
        super(PullComment, self).__init__(sender, date)
        self.proj = pullreq.to_proj_str
        self.ticket = ticket.ticket_id  # TODO: 统一:issue里显示的是名字，pr显示的是id。。。
        self.title = ticket.title
        self.content = PullComment._truncate(content)
        self.url = url  # TODO, uid

        self._target = pullreq.to_proj.name

    @property
    def type(self):
        return 'pull_comment'

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

migrate_pull_comment = {
    'sender': 'author',
    'content': 'text',
    'target': ('proj', lambda x: x.split(':')[0]),
    'scope': ('', lambda x: 'project'),  # only projects has
    'entry_id': 'ticket',
    'title': ('ticket', lambda x: 'PullRequest #%d' % x),    # don't know title
    # don't know title
    'entry_title': ('ticket', lambda x: 'PullRequest #%d' % x),
}
