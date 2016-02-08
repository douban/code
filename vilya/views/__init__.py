# -*- coding: utf-8 -*-

from __future__ import absolute_import

import json
from quixote.errors import TraversalError, AccessError

from vilya.libs.text import render_markdown
from vilya.libs.template import st, request
from vilya.views.uis.graph import GraphUI
from vilya.views.uis.browsefiles import BrowsefilesUI
from vilya.views.uis.sphinx_docs import SphinxDocsUI
from vilya.views.uis.docs import DocsUI
from vilya.views.uis.source import SourceUI
from vilya.views.uis.commit import CommitUI
from vilya.views.uis.pages import PagesUI
from vilya.views.uis.pull import PullUI, PullsUI
from vilya.views.uis.dashboard import DashboardUI
from vilya.views.uis.compare import CompareUI
from vilya.views.uis.comments import CommentUI
from vilya.views.uis.line_comments import LineCommentUI
from vilya.views.uis.code_review import CodeReviewUI
from vilya.views.uis.pr_comment import PrCommentUI
from vilya.views.uis.issue import IssueBoardUI, IssueCommentUI
from vilya.views.util import jsonize
from vilya.views.fair import FairUI
from vilya.views.hub.search_beta import SrcIndexUI, SearchUI
from vilya.models.feed import get_user_inbox, PAGE_ACTIONS_COUNT
from vilya.models.team import Team
from vilya.models.project import CodeDoubanProject
from vilya.models.project_issue import ProjectIssue
from vilya.models.user import User
from hub.static import get_static, set_content_type
from tasks import index_a_project_docs

ISSUES_COUNT_PER_PAGE = 5

_q_exports = ['hub', 'api', 'preview', 'settings', 'oauth', 'j', 'teams']


class StaticUI(object):
    _q_exports = []

    def __init__(self, request, path=''):
        self.path = path

    def _q_lookup(self, request, name):
        return StaticUI(request, '%s/%s' % (self.path, name))

    def __call__(self, request):
        set_content_type(request, self.path)

        r = get_static(self.path)
        return r


def _q_exception_handler(request, exception):
    if isinstance(exception, TraversalError):
        error = exception
        return st('/errors/404.html', **locals())
    if isinstance(exception, AccessError):
        error = exception
        return st('/errors/401.html', **locals())
    else:
        raise exception


def _q_index(request):
    user = request.user
    my_issues = []
    if user:
        username = user.username

        your_projects = CodeDoubanProject.get_projects(owner=username,
                                                       sortby='lru')
        watched_projects = CodeDoubanProject.get_watched_others_projects_by_user(  # noqa
            user=username,
            sortby='lru')

        teams = Team.get_by_user_id(user.name)
        actions = get_user_inbox(username).get_actions(
            stop=PAGE_ACTIONS_COUNT - 1)
        badge_items = user.get_badge_items()

        # pull request
        # your_tickets = user.get_user_pull_requests_rank(limit=5)
        your_tickets = user.get_user_submit_pull_requests(limit=5)

        # issue
        project_ids = CodeDoubanProject.get_ids(user.name)
        dt = {
            'state': "open",
            'limit': 5,
            'start': 0,
        }
        my_issues = ProjectIssue.gets_by_project_ids(project_ids, **dt)

        return st('newsfeed.html', **locals())
    return request.redirect("/teams/")


def _q_lookup(request, name):
    if name == 'static':
        return StaticUI(request)
    if name == 'favicon.ico':
        return StaticUI(request, '/favicon.ico')
    if name == 'fair':
        return FairUI(request)
    if CodeDoubanProject.exists(name):
        return CodeUI(name)
    if User.check_exist(name):
        return UserPrefixedRepoAdapter(name)


class UserPrefixedRepoAdapter(object):

    _q_exports = []

    def __init__(self, username):
        self.username = username

    def _q_lookup(self, request, url_part):
        proj_name = "%s/%s" % (self.username, url_part)
        if CodeDoubanProject.exists(proj_name):
            return CodeUI(proj_name)


class CodeUI:
    _q_exports = [
        'hooks', 'graph', 'commit', 'pull', 'newpull', 'comments',
        'compare', 'line_comments', 'browsefiles', 'pulls',
        'docs', 'remove', 'code_review', 'pr_comment', 'issues',
        'issue_comments', 're_index_docs', 'src_index',
        'search', 'pages', 'xdocs', 'dashboard',
    ]

    def __init__(self, proj_name):
        self.proj_name = proj_name

    def __call__(self, request):
        self.check_permission(request, self.proj_name)
        return SourceUI(self.proj_name, 'tree').direct_index(request)

    # FIXME: Is anyone using this?
    def hook_json(self, request):
        project = CodeDoubanProject.get_by_name(self.proj_name)
        data = map((lambda x: x.__dict__), project.hooks)
        return json.dumps(data)

    def _q_index(self, request):
        self.check_permission(request, self.proj_name)
        return SourceUI(self.proj_name, 'tree').direct_index(request)

    def _q_lookup(self, request, url_part):
        self.check_permission(request, self.proj_name)
        return SourceUI(self.proj_name, url_part)

    def check_permission(self, request, proj_name):
        project = CodeDoubanProject.get_by_name(proj_name)
        user = request.user
        if not project or \
           not user and project.intern_banned or \
           user and user.is_intern and project.intern_banned \
           and not project.is_admin(user.username):
            return request.redirect(User.create_login_url(request.url))

    @property
    def compare(self):
        return CompareUI(self.proj_name)

    @property
    def commit(self):
        return CommitUI(self.proj_name)

    @property
    def pages(self):
        return PagesUI(self.proj_name)

    @property
    def issues(self):
        return IssueBoardUI(self.proj_name)

    @property
    def issue_comments(self):
        return IssueCommentUI(self.proj_name)

    @property
    def graph(self):
        return GraphUI(self.proj_name)

    @property
    def pull(self):
        return PullUI(self.proj_name)

    @property
    def newpull(self):
        return PullUI(self.proj_name)

    @property
    def pulls(self):
        return PullsUI(self.proj_name)

    @property
    def dashboard(self):
        return DashboardUI(self.proj_name)

    @property
    def comments(self):
        return CommentUI(self.proj_name)

    @property
    def line_comments(self):
        return LineCommentUI(self.proj_name)

    @property
    def code_review(self):
        return CodeReviewUI(self.proj_name)

    @property
    def pr_comment(self):
        return PrCommentUI(self.proj_name)

    @property
    def browsefiles(self):
        return BrowsefilesUI(self.proj_name)

    @property
    def docs(self):
        return SphinxDocsUI(self.proj_name)

    @property
    def xdocs(self):
        project = CodeDoubanProject.get_by_name(self.proj_name)
        return DocsUI(project)

    @property
    def re_index_docs(self):
        project = CodeDoubanProject.get_by_name(self.proj_name)
        index_a_project_docs(project.id)
        return request.redirect("/%s/" % self.proj_name)

    @property
    def src_index(self):
        return SrcIndexUI(self.proj_name)

    @property
    def search(self):
        return SearchUI(self.proj_name)

    @jsonize
    def remove(self, request):
        if request.method == 'POST':
            user = request.user
            project = CodeDoubanProject.get_by_name(self.proj_name)
            if project.is_owner(user):
                parent_proj = project.get_forked_from()
                can_remove = False
                if parent_proj is None:
                    can_remove = True
                else:
                    can_remove = len(project.open_parent_pulls) == 0
                if can_remove:
                    project.delete()
                    return dict(r=1, err='')
                else:
                    return dict(r=0, err='该项目仍有未关闭的Pull request，请关闭后再删除项目。')  # noqa
        return dict(r=0, err='')


def preview(request):
    return render_markdown(request.get_form_var('text', '').decode('utf-8')).encode('utf-8')  # noqa
