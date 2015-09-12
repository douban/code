# -*- coding: utf-8 -*-

from vilya.models.actions.base import Action, ActionScope


# TODO
#            message=trunc_utf8(comment.content, 50, None),
#            proj=proj.name,
#            author=comment.author,
#            date=comment.created,
#            type='commit_comment',
#            ref=comment.ref,
#            url='/%s/commit/%s#%s' % (proj.name, comment.ref, self.uid)
class CommitComment(Action):
    def __init__(self, sender, date, proj_name, commit_ref, content, url):
        super(CommitComment, self).__init__(sender, date)
        self.proj = proj_name
        self.ref = commit_ref
        self.content = CommitComment._truncate(content)
        self.url = url  # TODO , uid?

    @property
    def type(self):
        return 'commit_comment'

    @property
    def scope(self):
        return ActionScope.project

    @property
    def target(self):
        return self.proj

    @property
    def entry_id(self):
        # 显示的时候 [:10]
        return self.ref

    @property
    def entry_title(self):
        return 'Commit comment in ' + self.ref[:10]

migrate_commit_comment = {
    'sender': 'author',
    'content': 'message',
    'target': 'proj',
    'scope': ('', lambda x: 'project'),  # only projects has commit_comment
    'entry_id': 'ref',
    'entry_title': ('ref', lambda x: 'Commit comment in ' + x[:10]),
}
