# -*- coding: utf-8 -*-

from __future__ import absolute_import
from quixote.errors import TraversalError, AccessError

from vilya.libs.template import st
from vilya.libs.signals import issue_signal, issue_comment_signal
from dispatches import dispatch

from vilya.models.elastic import SearchEngine
from vilya.models.elastic.issue_pr_search import IssueSearch
from vilya.models.project import CodeDoubanProject
from vilya.models.issue import Issue
from vilya.models.project_issue import ProjectIssue
from vilya.models.issue_comment import IssueComment
from vilya.models.tag import TagName
from vilya.models.team import Team
from vilya.models.milestone import Milestone
from vilya.views.util import http_method, jsonize
from vilya.views.issues.tags import TagsUI


ISSUES_COUNT_PER_PAGE = 25
_q_exports = []


def split_tags_str(tags):
    if not tags:
        return []
    tags = tags.split()
    return tags


def get_order_type(request, cookie_name):
    ''' order cookie getter/setter '''
    cookie_order = request.get_cookie(cookie_name)
    order = request.get_form_var('order', cookie_order)
    if order != 'hot':
        order = 'date'
    if order != cookie_order:
        request.response.set_cookie(cookie_name, order,
                                    expires="Thu 01-Jan-2020 00:00:00 GMT")
    return order


class IssueBoardUI(object):
    _q_exports = ['created_by', 'mentioned', 'assigned', 'new', 'create',
                  'search', 'milestones', 'tags']

    def __init__(self, proj_name):
        self.proj_name = proj_name
        self.project = CodeDoubanProject.get_by_name(self.proj_name)

        self._index = self._filter('repo')
        self._created_by = self._filter('created_by')
        self._assigned = self._filter('assigned')
        self._search = self._filter('search')

    def _q_index(self, request):
        return self._index(request)

    def created_by(self, request):
        return self._created_by(request)

    def assigned(self, request):
        return self._assigned(request)

    def search(self, request):
        return self._search(request)

    def _filter(self, list_type):
        ''' filter repo, created_by, assigned, search 4 list types. '''
        def index(request):
            if list_type == 'search':
                key_word = request.get_form_var('q', None)
                if not key_word:
                    return self._index(request)

            milestone_number = request.get_form_var('milestone')
            state = request.get_form_var('state', 'open')
            page = request.get_form_var('page', 1)
            project_name = self.proj_name
            user = request.user
            project = self.project
            order = get_order_type(request, 'project_issues_order')  # noqa 目前支持list_type = repo的sort_by
            n_open_issues = project.n_open_issues
            n_closed_issues = project.n_closed_issues
            n_everyone_issues = 0
            n_assigned_issues = 0
            n_created_issues = 0
            n_pages = 0
            selected_tag_names = request.get_form_var('tags', '')
            start = ISSUES_COUNT_PER_PAGE * (int(page) - 1)
            limit = ISSUES_COUNT_PER_PAGE

            is_closed_tab = None if state == "open" else True
            issue_list = []
            total_issues = 0
            opts = dict(project=project, state=state, start=start,
                        limit=limit, order=order)
            if selected_tag_names:
                selected_tag_names = selected_tag_names.split(',')
                tags = filter(None, [TagName.get_project_issue_tag(
                    name, project) for name in selected_tag_names])
                opts['tags'] = tags
            show_tags = project.get_group_tags(selected_tag_names)

            if milestone_number:
                milestone = Milestone.get_by_project(
                    project, number=milestone_number)
                opts['milestone'] = milestone

            # FIXME: why user or list_type ?
            if user or list_type in ('repo', 'search'):
                if list_type == 'search':
                    # FIXME: search with assigned or creator
                    search_result = IssueSearch.search_a_phrase(
                        key_word, self.project.id,
                        size=n_open_issues + n_closed_issues,
                        state=state) or []
                    search_issue_ids = []
                    if search_result and not search_result.get('error'):
                        search_issue_ids = [
                            id for id, in SearchEngine.decode(
                                search_result, ['issue_id'])]
                    # FIXME: is search_issue_ids int[]?
                    opts['issue_ids'] = search_issue_ids
                elif list_type == 'created_by':
                    opts['creator'] = user
                elif list_type == 'assigned':
                    opts['assignee'] = user
                # FIXME: update n_closed_issues & n_open_issues
                multi_dict = ProjectIssue.get_multi_by(**opts)
                issue_list = multi_dict['issues']
                total_issues = multi_dict['total']

                if user:
                    if list_type == 'repo':
                        n_assigned_issues = user.get_n_assigned_issues_by_project(project.id, state)  # noqa
                        n_created_issues = user.get_n_created_issues_by_project(project.id, state)  # noqa
                    elif list_type == 'created_by':
                        n_assigned_issues = user.get_n_assigned_issues_by_project(project.id, state)  # noqa
                        n_created_issues = total_issues
                    elif list_type == 'assigned':
                        n_assigned_issues = total_issues
                        n_created_issues = user.get_n_created_issues_by_project(project.id, state)  # noqa
                    elif list_type == 'search' and search_issue_ids:
                        n_assigned_issues = ProjectIssue.get_n_by_issue_ids_and_assignee_id(  # noqa
                            search_issue_ids, state, user.name)
                        n_created_issues = ProjectIssue.get_n_by_issue_ids_and_creator_id(  # noqa
                            search_issue_ids, state, user.name)
                n_pages = (total_issues - 1) / ISSUES_COUNT_PER_PAGE + 1

            # tags 的选择只会改变选中的filter的显示issue数
            if list_type in ('repo', 'search'):
                n_everyone_issues = total_issues
            else:
                n_everyone_issues = n_open_issues \
                    if state == "open" else n_closed_issues
            return st('issue/issues.html', **locals())
        return index

    # TODO
    def mentioned(self, request):
        list_type = 'mentioned'
        state = request.get_form_var('state', 'open')
        page = request.get_form_var('page', 1)
        project_name = self.proj_name
        user = request.user
        project = self.project
        n_open_issues = project.n_open_issues
        n_closed_issues = project.n_closed_issues
        n_everyone_issues = 0
        n_assigned_issues = 0
        n_created_issues = 0
        n_mentioned_issues = 0
        n_pages = 0
        issue_list = []
        total_issues = 0
        is_closed_tab = None if state == "open" else True
        if user:
            n_assigned_issues = user.get_n_assigned_issues_by_project(project.id, state)  # noqa
            n_created_issues = user.get_n_created_issues_by_project(project.id, state)  # noqa
        n_everyone_issues = n_open_issues \
            if state == "open" else n_closed_issues
        return st('issue/issues.html', **locals())

    def _q_lookup(self, request, issue_number):
        if issue_number.isdigit():
            return IssueUI(self.proj_name, issue_number)
        return request.redirect('/%s/issues' % self.proj_name)

    def new(self, request):
        project_name = self.proj_name
        project = self.project
        user = request.user
        tags = project.tags
        error = request.get_form_var('error')
        teams = Team.get_all_team_uids()
        return st('issue/new.html', **locals())

    def create(self, request):
        if request.method == 'POST':
            user = request.user
            if not user:
                raise AccessError
            project = request.get_form_var('project')
            title = request.get_form_var('title', '').decode('utf-8')
            description = request.get_form_var('body', '').decode('utf-8')
            tags = request.get_form_var('issue_tags', [])
            if isinstance(tags, list):
                tags = [tag.decode('utf-8') for tag in tags if tag]
            elif isinstance(tags, basestring):
                tags = [tags.decode('utf-8')]

            if not project:
                raise TraversalError
            if not title.strip():
                return request.redirect('/%s/issues/new?error=empty' % project)
            project = CodeDoubanProject.get_by_name(project)
            pissue = ProjectIssue.add(title, description, user.name,
                                      project=project.id)
            pissue.add_tags(tags, pissue.project_id)
            # TODO: 重构feed后取消信号发送
            issue_signal.send(author=user.name, content=description,
                              issue_id=pissue.issue_id)
            dispatch('issue', data={
                     'sender': user.name,
                     'content': description,
                     'issue': pissue
                     })
            return request.redirect(pissue.url)
        project_name = self.proj_name
        return request.redirect('/%s/issues' % project_name)

    @property
    def milestones(self):
        return MilestonesUI(self.project)

    @property
    def tags(self):
        return TagsUI(self.project)


class IssueUI(object):
    _q_exports = ['comment', 'assign', 'tag', 'upvote', 'join', 'leave',
                  'milestone']

    def __init__(self, proj_name, issue_number):
        self.target = CodeDoubanProject.get_by_name(proj_name)
        self.issue_number = issue_number

        project_issue = ProjectIssue.get(self.target.id,
                                         number=self.issue_number)
        self.issue_id = project_issue.issue_id
        self.issue = Issue.get_cached_issue(self.issue_id)
        self.issue_template = 'issue/issue.html'

    def _q_index(self, request):
        show_close = True
        target = self.target
        issue = self.issue
        user = request.user
        current_user = request.user
        author = issue.creator
        i_am_author = user and issue.creator_id == user.username
        i_am_admin = user and target.is_admin(user.name)
        has_user_voted = issue.has_user_voted(user.name) if user else False
        vote_count = issue.vote_count
        teams = Team.get_all_team_uids()
        return st(self.issue_template, **locals())

    @jsonize
    def upvote(self, request):
        issue = self.issue
        user = request.user
        return upvote_action(issue, user, request)

    @jsonize
    def comment(self, request):
        target = self.target
        issue = self.issue
        issue_id = self.issue_id
        current_user = request.user

        if request.method == 'POST':
            content = request.get_form_var('content', '').decode('utf-8')
            user = request.user
            user = user.name if user else None
            if user:
                author = user
                if content.strip():
                    comment = issue.add_comment(content, user)
                    issue.add_participant(user)
                    html = st('/widgets/issue/issue_comment.html', **locals())
                else:
                    return {'error': 'Content is empty'}

                if request.get_form_var('comment_and_close'):
                    issue.close(author)
                    # TODO: 重构feed后取消信号发送
                    issue_signal.send(author=author, content=content,
                                      issue_id=issue_id)
                    dispatch('issue', data={
                             'sender': author,
                             'content': content,
                             'issue': issue,
                             })
                    return dict(r=0, reload=1, redirect_to=issue.url)
                elif request.get_form_var('comment_and_open'):
                    issue.open()
                    # TODO: 重构feed后取消信号发送
                    issue_signal.send(author=author, content=content,
                                      issue_id=issue_id)
                    dispatch('issue', data={
                             'sender': author,
                             'content': content,
                             'issue': issue,
                             })
                    return dict(r=0, reload=1, redirect_to=issue.url)
                elif content:
                    issue_comment_signal.send(author=author,
                                              content=comment.content,
                                              issue_id=comment.issue_id,
                                              comment_id=comment.id)
                    dispatch('issue_comment', data={
                             'sender': author,
                             'content': comment.content,
                             'issue': issue,
                             'comment': comment})
                participants = issue.participants

                teams = Team.get_all_team_uids()

                participants_html = st('/widgets/participation.html',
                                       **locals())  # FIXME: locals()?
                return dict(
                    r=0, html=html, participants_html=participants_html)
        return request.redirect(issue.url)

    def tag(self, request):
        target = self.target
        issue = self.issue
        if request.method == 'POST':
            user = request.user
            user = user.name if user else None
            if user:
                tags = request.get_form_var('tags', [])
                if isinstance(tags, basestring):
                    tags = split_tags_str(tags.decode('utf8'))
                tags_orig = [tag.name for tag in issue.tags]
                tags_to_add = list(set(tags).difference(tags_orig))
                tags_to_del = list(set(tags_orig).difference(tags))
                issue.add_tags(tags_to_add, target.id, user)
                issue.remove_tags(tags_to_del, target.id)
        return request.redirect(issue.url)

    def milestone(self, request):
        issue = self.issue
        if request.method == 'POST':
            user = request.user
            if not user:
                return request.redirect(issue.url)
            milestone = request.get_form_var('milestone', '')
            milestone_title = request.get_form_var('milestone_title', '')
            if milestone == 'new' and milestone_title:
                issue.add_milestone(user, name=milestone_title)
            elif milestone == 'clear':
                issue.remove_milestone()
            else:
                issue.add_milestone(user, milestone_id=milestone)
        return request.redirect(issue.url)

    @http_method(methods=["POST"])
    @jsonize
    def join(self, request):
        issue = self.issue
        user = request.user
        if user:
            issue.add_participant(user.name)
            participants = issue.participants
            teams = Team.get_all_team_uids()
            participants_html = st('/widgets/participation.html',
                                   participants=participants, teams=teams)
            return dict(r=0, participants_html=participants_html)
        return dict(r=1)

    @http_method(methods=["POST"])
    @jsonize
    def leave(self, request):
        issue = self.issue
        user = request.user
        if user:
            if user.name == issue.creator_id:
                return dict(r=1, msg="Can't leave the issue created by you.")
            issue.delete_participant(user.name)
            participants = issue.participants
            teams = Team.get_all_team_uids()
            participants_html = st('/widgets/participation.html',
                                   participants=participants, teams=teams)
            return dict(r=0, participants_html=participants_html)
        return dict(r=1)

    def assign(self, request):
        issue = self.issue
        if request.method == 'POST':
            user = request.user
            if user:
                assignee = request.get_form_var('assignee', '').decode('utf-8')
                issue.assign(assignee)
        return request.redirect(issue.url)


class IssueCommentUI(object):
    _q_exports = ['edit', 'delete']

    def __init__(self, proj_name):
        self.proj_name = proj_name
        self.project = CodeDoubanProject.get_by_name(self.proj_name)
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
        pissue = Issue.get_cached_issue(issue_id)
        pissue.update_rank_score()
        return {'r': 1}

    @jsonize
    def edit(self, request):
        if request.method == 'POST':
            user = request.user
            current_user = request.user
            if self.comment.author_id != user.username:
                raise AccessError
            project = self.project
            content = request.get_form_var(
                'pull_request_comment', '').decode('utf-8')
            self.comment.update(content)
            comment = IssueComment.get(self.comment.id)
            author = user
            target = project
            return dict(
                r=0, html=st('/widgets/issue/issue_comment.html', **locals()))


class MilestonesUI(object):
    _q_exports = []

    def __init__(self, project):
        self.project = project

    def _q_index(self, request):
        project = self.project
        milestones = project.issue_milestones
        return st('/issue/milestones.html', **locals())


def upvote_action(issue, user, request):
    msg = ''
    count = None
    action = 0
    if not user:
        msg = "You should login before voting on any issue!"
    elif issue.is_closed:
        msg = "You can not vote or unvote a closed issue!"
    elif issue.creator_id == user.name:
        msg = "You can not vote on issues created by yourself!"
    elif request.method == 'PUT':
        count = issue.upvote_by_user(user.name)
        action = 1
    elif request.method == 'DELETE':
        count = issue.cancel_upvote_by_user(user.name)
        action = -1
    else:
        action = 0
        msg = 'Unsupport Method'

    if count is None:
        count = issue.vote_count

    return {
        'action': action,
        'count': count,
        'msg': msg,
    }
