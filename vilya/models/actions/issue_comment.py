# -*- coding: utf-8 -*-

from vilya.models.actions.base import Action, ActionScope


# TODO
#            'date': self.now(),
#            'url': issue.url,
#            'number': issue.number,
#            'target_name': target.name,
#            'target_url': target.url,
#            'receiver': issue.creator_id,
#            'title': issue.title,
#            'author': sender,
#            'text': content,
#            'type': 'issue_comment',
class IssueComment(Action):
    def __init__(self, sender, date, target, issue, content):
        super(IssueComment, self).__init__(sender, date)
        self.target_name = target.name
        self.target_type = issue.target_type
        self.target_url = target.url
        self.title = issue.title
        self.number = issue.number
        self.content = IssueComment._truncate(content)
        self.url = issue.url

    @property
    def type(self):
        return 'issue_comment'

    @property
    def scope(self):
        scope = ActionScope.getScope(self.target_type)
        return scope if scope else ActionScope.project

    @property
    def target(self):
        return self.target_name

    @property
    def entry_id(self):
        return self.number

    @property
    def entry_title(self):
        return '#%d %s' % (self.number, self.title)


def _migrate_scope(url):
    ''' hack from target_url '''
    urls = url.split('/')
    scope = 'project'
    if urls[1] == 'fair':
        scope = 'fair'
    elif urls[1] == 'hub' and urls[2] == 'team':
        scope = 'team'
    elif urls[1] == 'teams':
        scope = 'team'
    return scope

migrate_issue_comment = {
    'sender': 'author',
    'content': 'text',
    'target': 'target_name',
    'target_type': ['target_url', _migrate_scope],
    'scope': ['target_url', _migrate_scope],
    'entry_id': 'number',
    'entry_title': 'title',
}
