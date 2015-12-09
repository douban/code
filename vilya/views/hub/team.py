# -*- coding: utf-8 -*-

import re

import requests
from quixote.errors import TraversalError, AccessError

from vilya.libs.template import st
# TODO: remove signals
from vilya.libs.signals import team_joined_signal
from vilya.libs.signals import (team_add_member_signal,
                                issue_signal)

from dispatches import dispatch
from vilya.views.util import http_method, jsonize

from vilya.models.user import User
from vilya.models.team import Team, TeamUserRelationship
from vilya.models.consts import TEAM_IDENTITY_INFO, TEAM_MEMBER
from vilya.models.project import CodeDoubanProject
from vilya.models.feed import get_team_feed, PAGE_ACTIONS_COUNT
from vilya.models.issue import Issue
from vilya.models.team_issue import TeamIssue
from vilya.models.issue_comment import IssueComment
from vilya.models.tag import Tag, TAG_TYPE_TEAM_ISSUE
from vilya.models.consts import UPLOAD_URL

from vilya.views.uis.pull import TeamPullsUI
from vilya.views.uis.issue import IssueUI, get_order_type

ISSUES_COUNT_PER_PAGE = 25
_q_exports = []


class TeamUI(object):
    _q_exports = [
        "settings", "pulls", "add_project", "remove_project",
        "join", "leave", "add_user", "remove_user", "upload_profile",
        "remove", "issues", "issue_comments", "news", "groups",
    ]

    def __init__(self, request, team_uid):
        self.team_uid = team_uid
        self.request = request

    @property
    def pulls(self):
        team = Team.get_by_uid(self.team_uid)
        if not team:
            raise TraversalError
        return TeamPullsUI(self.team_uid)

    @property
    def issues(self):
        team = Team.get_by_uid(self.team_uid)
        if not team:
            raise TraversalError
        return TeamIssueBoardUI(self.team_uid)

    @property
    def issue_comments(self):
        team = Team.get_by_uid(self.team_uid)
        if not team:
            raise TraversalError
        return TeamIssueCommentUI(self.team_uid)

    @property
    def groups(self):
        team = Team.get_by_uid(self.team_uid)
        if not team:
            raise TraversalError
        return TeamGroupsUI(team)

    @http_method(methods=["POST"])
    @jsonize
    def join(self, request):
        user = request.user
        team = Team.get_by_uid(self.team_uid)
        if not user or not team:
            return dict(r=1)

        team.add_user(user, TEAM_MEMBER)
        team_joined_signal.send(user.name,
                                team_id=team.id,
                                team_uid=team.uid,
                                team_name=team.name)
        return dict(r=0)

    @http_method(methods=["POST"])
    @jsonize
    def upload_profile(self, request):
        user = request.user
        team = Team.get_by_uid(self.team_uid)
        if not user and not team:
            return dict(r=1)
        if team and not team.is_owner(user.name):
            return dict(r=1)

        upload_url = request.get_form_var('url', '')
        hash_png = request.get_form_var('hash', '')
        profile = {'origin': upload_url}
        if upload_url and hash_png:
            rsize_url = '{0}/r/{1}?w=100&h=100'.format(UPLOAD_URL, hash_png)
            r = requests.get(rsize_url)
            r.raise_for_status()
            profile.update({'icon': r.text})
        team.profile = profile
        return dict(r=0)

    @http_method(methods=["POST"])
    @jsonize
    def leave(self, request):
        user = request.user
        team = Team.get_by_uid(self.team_uid)
        if not user or not team:
            return dict(r=1)

        team.remove_user(user)
        return dict(r=0)

    def add_project(self, request):
        user = request.user
        team = Team.get_by_uid(self.team_uid)
        if not user and not team:
            return request.redirect('/')
        if team and not team.is_owner(user.name):
            return request.redirect(team.url)

        project_name = request.get_form_var('project_name') or ''
        project = CodeDoubanProject.get_by_name(project_name)
        error = ''
        if request.method == 'POST':
            if not project_name:
                error = 'project_name_not_exists'
            elif not project:
                error = 'project_not_exists'
            else:
                team.add_project(project)
                return request.redirect(team.url)
        return st('/teams/team_add_project.html', **locals())

    @http_method(methods=["POST"])
    @jsonize
    def remove_project(self, request):
        user = request.user
        team = Team.get_by_uid(self.team_uid)
        if not user or not team:
            return dict(r=1)

        if not team.is_owner(user.name):
            return dict(r=1)

        project_name = request.get_form_var('project_name', '')
        project = CodeDoubanProject.get_by_name(project_name)
        if not project:
            return dict(r=1)

        team.remove_project(project)
        return dict(r=0)

    @http_method(methods=["POST"])
    @jsonize
    def add_user(self, request):
        user = request.user
        team = Team.get_by_uid(self.team_uid)
        if not user or not team:
            return dict(r=1, error="team不存在")

        user_id = request.get_form_var('user_id', '')
        identity = int(request.get_form_var('identity', 0))

        if not team.is_owner(user.name) \
                or identity not in TEAM_IDENTITY_INFO.keys():
            return dict(r=1, error="没有权限")

        rl = TeamUserRelationship.get(team_id=team.id, user_id=user_id)
        if not rl:
            team.add_user(User(user_id), identity)
        elif identity == rl.identity:
            return dict(r=1, error="该用户已存在")
        elif rl.is_owner and team.n_owners == 1:
            return dict(r=1, error="只剩一个creator, 不能改变身份")
        else:
            rl.identity = identity
            rl.save()

        avatar_url = User(user_id).avatar_url
        team_add_member_signal.send(
            user.name, team_uid=team.uid, team_name=team.name,
            receiver=user_id, identity=TEAM_IDENTITY_INFO[identity]["name"])
        return dict(r=0, uid=user_id, avatar_url=avatar_url)

    @http_method(methods=["POST"])
    @jsonize
    def remove_user(self, request):
        user = request.user
        if not user:
            return dict(r=1, error="用户未登录")

        team = Team.get_by_uid(self.team_uid)
        if not team:
            return dict(r=1, error="team不存在")

        user_id = request.get_form_var('user_id', '')

        if not team.is_owner(user.name):
            return dict(r=1, error="没有权限")
        rl = TeamUserRelationship.get(team_id=team.id, user_id=user_id)
        if not rl:
            return dict(r=1, error="用户未加入team")
        elif rl.is_owner and team.n_owners == 1:
            return dict(r=1, error="只剩一个creator不能删除")
        else:
            rl.delete()
        return dict(r=0)

    @http_method(methods=["POST"])
    @jsonize
    def remove(self, request):
        team = Team.get_by_uid(self.team_uid)
        if not team:
            return dict(r=1)

        user = request.user
        if not user or not team.is_owner(user.name):
            return dict(r=1)

        team.delete()
        return {'r': 0}

    def news(self, request):
        user = request.user
        team = Team.get_by_uid(self.team_uid)
        if not team:
            raise TraversalError
        feed = get_team_feed(team.id)
        actions = feed.get_actions(stop=PAGE_ACTIONS_COUNT - 1)
        projects = team.projects
        is_admin = False
        if user and team.is_owner(user.name):
            is_admin = True
        return st('/teams/news.html', **locals())

    def settings(self, request):
        user = request.user
        team = Team.get_by_uid(self.team_uid)
        if not team:
            raise TraversalError
        projects = team.projects

        input_uid = request.get_form_var('uid', '')
        input_name = request.get_form_var('name', '')
        input_description = request.get_form_var('description', '')

        error = ''
        if request.method == "POST":
            if not user:
                return request.redirect("/")

            if not team.is_owner(user.name):
                return request.redirect(team.url)

            teams = Team.gets()
            team_uid_pattern = re.compile(r'[a-zA-Z0-9\_]*')
            if not input_uid:
                error = 'uid_not_exists'
            elif not input_name:
                error = 'name_not_exists'
            elif input_uid != re.findall(team_uid_pattern, input_uid)[0]:
                error = 'invilid_uid'
            elif input_uid in [t.uid for t in teams] and team.uid != input_uid:
                error = 'uid_existed'
            elif input_name in [t.name for t in teams] \
                 and team.name != input_name:
                error = 'name_existed'
            else:
                team.update(input_uid, input_name, input_description)
                return request.redirect("/hub/team/%s/settings" % input_uid)
        return st('/teams/team_settings.html', **locals())

    def _q_index(self, request):
        user = request.user
        team = Team.get_by_uid(self.team_uid)
        if not team:
            raise TraversalError
        projects = team.projects
        is_admin = False
        if user and team.is_owner(user.name):
            is_admin = True
        return st('/teams/team.html', **locals())

    def _q_lookup(self, request, url_part):
        return TeamUI(request, url_part)


def _q_lookup(request, team_uid):
    return TeamUI(request, team_uid)


class TeamIssueBoardUI(object):
    _q_exports = ['created_by', 'mentioned', 'assigned', 'new', 'create']
    cls = TeamIssue

    def __init__(self, team_uid):
        self.team_uid = team_uid
        self.team = Team.get_by_uid(self.team_uid)

    def _q_index(self, request):
        user = request.user
        team = self.team
        page = request.get_form_var('page', 1)
        state = request.get_form_var("state", "open")
        order = get_order_type(request, 'team_issues_order')

        team_issues = []

        selected_tag_names = request.get_form_var('tags', '')
        if selected_tag_names:
            selected_tag_names = selected_tag_names.split(',')
            issue_ids = Tag.get_type_ids_by_names_and_target_id(
                TAG_TYPE_TEAM_ISSUE,
                selected_tag_names,
                team.id)
            team_issues = self.cls.gets_by_issue_ids(issue_ids, state)
        else:
            team_issues = self.cls.gets_by_target(team.id, state, order=order)

        n_team_issue = len(team_issues)
        show_tags = team.get_group_tags(selected_tag_names)
        is_closed_tab = None if state == "open" else True
        n_pages = 1
        # TODO: 分页
        return st('issue/team_issues.html', **locals())

    def _q_lookup(self, request, issue_number):
        if issue_number.isdigit():
            return TeamIssueUI(self.team_uid, issue_number)
        return request.redirect(self.team.url + 'issues')

    def created_by(self, request):
        return request.redirect(self.team.url + 'issues')

    def mentioned(self, request):
        return request.redirect(self.team.url + 'issues')

    def assigned(self, request):
        return request.redirect(self.team.url + 'issues')

    def new(self, request):
        user = request.user
        current_user = request.user
        team = self.team
        tags = team.tags
        error = request.get_form_var('error')
        teams = Team.get_all_team_uids()
        return st('issue/new_team_issue.html', **locals())

    def create(self, request):
        if request.method == 'POST':
            user = request.user
            if not user:
                raise AccessError
            team = self.team
            if not team:
                raise TraversalError
            title = request.get_form_var('title', '').decode('utf-8')
            description = request.get_form_var('body', '').decode('utf-8')
            tags = request.get_form_var('issue_tags', [])
            if isinstance(tags, list):
                tags = [tag.decode('utf-8') for tag in tags if tag]
            elif isinstance(tags, basestring):
                tags = [tags.decode('utf-8')]

            if not(title and description):
                return request.redirect('../new?error=empty')

            tissue = self.cls.add(title, description, user.name, team=team.id)
            tissue.add_tags(tags, tissue.team_id)
            # TODO: 重构feed后删除这个signal
            issue_signal.send(author=user.name, content=description,
                              issue_id=tissue.issue_id)
            dispatch('issue', data={
                     'sender': user.name,
                     'content': description,
                     'issue': tissue,
                     })
            return request.redirect(tissue.url)
        return request.redirect(self.team.url + 'issues')


class TeamIssueUI(IssueUI):
    _q_exports = IssueUI._q_exports

    def __init__(self, team_uid, issue_number):
        self.target = Team.get_by_uid(team_uid)
        self.issue_number = issue_number

        team_issue = TeamIssue.get(self.target.id, number=self.issue_number)
        self.issue_id = team_issue.issue_id
        self.issue = Issue.get_cached_issue(self.issue_id)
        self.issue_template = 'issue/team_issue.html'


# TODO: 继承自 IssueCommentUI
class TeamIssueCommentUI(object):
    _q_exports = ['edit', 'delete']
    cls = TeamIssue

    def __init__(self, team_uid):
        self.team_uid = team_uid
        self.team = Team.get_by_uid(self.team_uid)
        self.comment = None

    def _q_lookup(self, request, comment_id):
        comment = IssueComment.get(comment_id)
        if not comment:
            raise TraversalError(
                "Unable to find issue comment %s" % comment_id)
        else:
            self.comment = comment
            return self

    @jsonize
    def delete(self, request):
        user = request.user
        if self.comment.author_id != user.username:
            raise AccessError
        issue_id = self.comment.issue_id
        ok = self.comment.delete()
        if not ok:
            return {'r': 0}
        tissue = Issue.get_cached_issue(issue_id)
        tissue.update_rank_score()
        return {'r': 1}

    @jsonize
    def edit(self, request):
        if request.method == 'POST':
            user = request.user
            current_user = request.user
            if self.comment.author_id != user.username:
                raise AccessError
            team = self.team
            content = request.get_form_var(
                'pull_request_comment', '').decode('utf-8')
            self.comment.update(content)
            comment = IssueComment.get(self.comment.id)
            author = user
            target = team
            return dict(r=0,
                        html=st('/widgets/issue/issue_comment.html',
                                **locals()))


class TeamGroupsUI(object):
    _q_exports = ['new']

    def __init__(self, team):
        self.team = team

    def _q_index(self, request):
        from vilya.models.team_group import TeamGroup
        context = {}
        team = self.team
        context["request"] = request
        context["team"] = team
        context["user"] = request.user
        if request.method == "POST":
            user = request.user
            name = request.get_form_var('group[name]')
            desc = request.get_form_var('group[description]', '')
            perm = request.get_form_var('group[permission]', 'pull')
            g = team.create_group(name=name,
                                  creator_id=user.name,
                                  description=desc,
                                  permission=TeamGroup.translate_perm(perm))
            return request.redirect(self.team.url + 'groups/%s' % g.name)
        groups = TeamGroup.gets_by(team_id=team.id)
        context["groups"] = groups
        return st('/teams/groups.html', **context)

    def _q_lookup(self, request, part):
        from vilya.models.team_group import TeamGroup
        team = self.team
        group = TeamGroup.get(team_id=team.id, name=part)
        if not group:
            raise TraversalError
        return TeamGroupUI(group)

    def new(self, request):
        context = {}
        team = self.team
        context["request"] = request
        context["team"] = team
        return st('/teams/new_group.html', **context)


class TeamGroupUI(object):
    _q_exports = ['settings', 'owners', 'members', 'projects']

    def __init__(self, group):
        self.group = group

    def _q_index(self, request):
        context = {}
        group = self.group
        team = group.team
        context["request"] = request
        context["team"] = team
        context["group"] = group
        context["user"] = request.user
        return st('/teams/group.html', **context)

    @property
    def settings(self):
        return TeamGroupSettingsUI(self.group)

    @property
    def owners(self):
        return TeamGroupOwnersUI(self.group)

    @property
    def members(self):
        return TeamGroupMembersUI(self.group)

    @property
    def projects(self):
        return TeamGroupProjectsUI(self.group)


class TeamGroupSettingsUI(object):
    _q_exports = []

    def __init__(self, group):
        self.group = group

    def _q_index(self, request):
        context = {}
        group = self.group
        team = group.team
        context["request"] = request
        context["team"] = team
        context["group"] = group
        if request.method == "POST":
            desc = request.get_form_var('group[description]', '')
            perm = request.get_form_var('group[permission]', 'pull')
            group.description = desc
            group.permission = group.translate_perm(perm)
            group.save()
        return st('/teams/group_settings.html', **context)


class TeamGroupOwnersUI(object):
    _q_exports = ['leave', 'join']

    def __init__(self, group):
        self.group = group

    def leave(self, request):
        user = request.user
        group = self.group
        group.remove_user(user_id=user.name)
        return request.redirect("%sgroups/" % group.team.url)

    def join(self, request):
        user = request.user
        group = self.group
        group.add_user(user_id=user.name)
        return request.redirect(group.url)


class TeamGroupMembersUI(object):
    _q_exports = ['destroy']

    def __init__(self, group):
        self.group = group

    def _q_index(self, request):
        group = self.group
        member = request.get_form_var('member')
        if member:
            group.add_user(user_id=member)
        return request.redirect(group.url)

    def destroy(self, request):
        group = self.group
        member = request.get_form_var('member')
        if member:
            group.remove_user(user_id=member)
        return request.redirect(group.url)


class TeamGroupProjectsUI(object):
    _q_exports = ['destroy']

    def __init__(self, group):
        self.group = group

    def _q_index(self, request):
        group = self.group
        project = request.get_form_var('project')
        p = CodeDoubanProject.get_by_name(project) if project else None
        if project and p:
            group.add_project(project_id=p.id)
        return request.redirect(group.url)

    def destroy(self, request):
        group = self.group
        project = request.get_form_var('project')
        p = CodeDoubanProject.get_by_name(project) if project else None
        if project and p:
            group.remove_project(project_id=p.id)
        return request.redirect(group.url)
