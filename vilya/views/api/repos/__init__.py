# -*- coding: utf-8 -*-
import json


from vilya.libs import api_errors
from vilya.models.project import CodeDoubanProject
from vilya.views.api.utils import RestAPIUI, api_require_login, jsonize
from vilya.views.api.repos.product import ProductUI
from vilya.views.api.repos.summary import SummaryUI
from vilya.views.api.repos.intern import InternUI
from vilya.views.api.repos.default_branch import DefaultBranchUI
from vilya.views.api.repos.commits import CommitsUI
from vilya.views.api.repos.post_receive import PostReceiveUI
from vilya.views.api.repos.git2svn import GIT2SVNUI
from vilya.views.api.repos.svn2git import SVN2GITUI
from vilya.views.api.repos.pulls import PullsUI
from vilya.views.api.repos.issues import IssuesUI
from vilya.views.api.repos.contents import ContentsUI
from vilya.views.api.repos.push import PushUI
from vilya.views.api.repos.watchers import WatchersUI

_q_exports = []


def _q_lookup(request, name):
    return RepositoryUI(name)


def _q_access(request):
    request.response.set_content_type('application/json; charset=utf-8')


class RepositoryUI(object):
    _q_exports = [
        'lang_stats', 'forks', 'pulls', 'summary',
        'committers', 'name', 'owner', 'product',
        'intern_banned', 'default_branch', 'commits',
        'post_receive', 'svn2git', 'git2svn', 'issues',
        'contents', 'can_push', 'watchers'
    ]

    def __init__(self, name):
        self.name = name
        self.repo = CodeDoubanProject.get_by_name(self.name)

    def __call__(self, request):
        return self._q_index(request)

    @jsonize
    def _q_index(self, request):
        if not self.repo:
            raise api_errors.NotFoundError("repo")
        return {}

    def _q_access(self, request):
        self.method = request.method

    def _q_lookup(self, request, part):
        name = "%s/%s" % (self.name, part)
        if not CodeDoubanProject.exists(name):
            raise api_errors.NotFoundError("repo")
        return RepositoryUI(name)

    @jsonize
    def lang_stats(self, request):
        if not self.repo:
            raise api_errors.NotFoundError
        if self.method == 'POST':
            language = request.get_form_var('language', '')
            languages = request.get_form_var('languages', '[]')
            try:
                languages = json.loads(languages)
            except ValueError:
                raise api_errors.NotJSONError
            self.repo.language = language
            self.repo.languages = languages
            return {}
        else:
            return dict(language=self.repo.language,
                        languages=self.repo.languages)

    @property
    def forks(self):
        return ForksUI(self.repo)

    @property
    def pulls(self):
        return PullsUI(self.repo)

    @property
    def product(self):
        return ProductUI(self.repo)

    @property
    def summary(self):
        return SummaryUI(self.repo)

    @property
    def intern_banned(self):
        return InternUI(self.repo)

    @property
    def can_push(self):
        return PushUI(self.repo)

    @property
    def default_branch(self):
        return DefaultBranchUI(self.repo)

    @property
    def commits(self):
        return CommitsUI(self.repo)

    @property
    def post_receive(self):
        return PostReceiveUI(self.repo)

    @property
    def svn2git(self):
        return SVN2GITUI(self.repo)

    @property
    def git2svn(self):
        return GIT2SVNUI(self.repo)

    @property
    def issues(self):
        return IssuesUI(self.repo)

    @property
    def contents(self):
        return ContentsUI(self.repo)

    @property
    def watchers(self):
        return WatchersUI(self.repo)


class ForksUI(RestAPIUI):
    _q_exports = []
    _q_methods = ['get', 'post']

    def __init__(self, repo):
        self.repo = repo

    @api_require_login
    def post(self, request):
        repo = self.repo
        fork_repo = repo.new_fork(self.user.name)
        if not fork_repo:
            # FIXME: repository exists
            return []
        return fork_repo.as_dict()

    def get(self, request):
        fork_repos = self.repo.get_forked_projects()
        return [project.get_info(without_commits=True)
                for project in fork_repos]
