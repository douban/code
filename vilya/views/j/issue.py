# -*- coding: utf-8 -*-

from quixote.errors import TraversalError
from vilya.views.libs.template import st
from vilya.views.libs.text import parse_emoji, render_markdown_with_project, render_markdown
from vilya.views.models.issue import Issue
from vilya.views.models.project import CodeDoubanProject
from vilya.views.models.tag import TagName, Tag, TAG_TYPE_PROJECT_ISSUE, TAG_TYPE_TEAM_ISSUE
from vilya.views.models.team import Team
from vilya.views.util import jsonize

_q_exports = ['delete_tag']


def _q_lookup(request, uid):
    if uid.isdigit():
        issue = Issue.get_cached_issue(uid)
        if issue:
            return IssueUI(issue)
    raise TraversalError


@jsonize
def delete_tag(request):
    # FIXME: ugly
    if request.method == "POST":
        user = request.user
        if not user:
            return {'r': 0, 'msg': '未登录，请先登录'}
        tag_name = request.get_form_var('tag_name', '').decode('utf-8')
        tag_type = request.get_form_var('tag_type', '')
        tag_target_id = request.get_form_var('tag_target_id', '')

        if not tag_name:
            return {'r': 0, 'msg': 'tag不能为空'}
        try:
            tag_type, tag_target_id = int(tag_type), int(tag_target_id)
        except:
            return {'r': 0, 'msg': '错误的数据类型'}

        if tag_type == TAG_TYPE_PROJECT_ISSUE:
            target = CodeDoubanProject.get(tag_target_id)
        elif tag_type == TAG_TYPE_TEAM_ISSUE:
            target = Team.get(tag_target_id)
        else:
            return {'r': 0, 'msg': '错误的数据类型'}

        if not target.is_admin(user.name):
            return {'r': 0, 'msg': '没有操作权限'}

        tname = TagName.get_by_name_and_target_id(
            tag_name, tag_type, target.id)
        if not tname:
            return {'r': 0, 'msg': 'tag不存在'}

        tags = Tag.gets_by_tag_id(tname.id)
        for tag in tags:
            tag.delete()
        tname.delete()
        return {'r': 1, 'msg': '删除成功'}


class IssueUI(object):
    _q_exports = ['edit', ]

    def __init__(self, issue):
        self.target = issue.target
        self.issue = issue

    @jsonize
    def edit(self, request):
        if request.method == 'POST':
            title = request.get_form_var('title', '').decode('utf-8')
            if not title.strip():
                return {'r': 1}
            content = request.get_form_var('content', '').decode('utf-8')
            user = request.user
            user = user.name if user else None
            if self.issue and user == self.issue.creator_id:
                self.issue.update(title, content)
                if self.issue == "project":
                    content_html = render_markdown_with_project(
                        content, self.target.name)
                else:
                    content_html = render_markdown(content)
                content_html += st('/widgets/markdown_checklist.html',
                                   **locals())
                return {'r': 0,
                        'title': title,
                        'content': content,
                        'title_html': parse_emoji(title),
                        'content_html': content_html}
        return {'r': 1}
