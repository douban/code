# -*- coding: utf-8 -*-
from __future__ import absolute_import
import json
from cgi import escape

from quixote.errors import TraversalError

from vilya.models.project import CodeDoubanProject
from vilya.models.user import User, get_author_by_email
from vilya.models.consts import API_ENDPOINTS
from vilya.models.team import Team

from vilya.views.api.git import GitUI, CommitsUI
from vilya.views.api.issue import IssuesUI, IssueUI
from vilya.views.api.pulls import PullsUI, MyPullsUI, PullUI
from vilya.views.api.statuses import StatusesUI
from vilya.views.api.files import FilesUI
from vilya.views.api.utils import jsonize
from vilya.views.api.center import CenterUI
from vilya.views.api.diff import PullDiffUI

from vilya.libs import api_errors
from vilya.libs.api_errors import CodeAPIError
from vilya.libs.auth.check_auth import check_auth
from vilya.libs.auth.oauth import OAuthError
from vilya.libs.text import parse_emoji
from vilya.libs.text import highlight_code, format_md_or_rst
from vilya.libs.reltime import compute_relative_time
from vilya.config import DOMAIN


_q_exports = ['repos', 'autocomplete_repos', 'autocomplete_users',
              'card_info', 'svn2git', 'users', 'user', 'gists', 'gist',
              'get_code_version', 'team', 'timeline', 'mute', 'notifications',
              'user_setting', 'teams', 'center']


center = CenterUI()


@jsonize
def _q_index(request):
    return API_ENDPOINTS


def _q_access(request):
    check_auth(request)
    if 'svn2git' not in request.get_url():
        request.response.set_content_type('application/json; charset=utf8')


def _q_lookup(request, proj_name):
    if proj_name == 'my_pulls':
        return MyPullsUI(request)
    return APIUI(request, proj_name)


def autocomplete_repos(request):
    """search for projects"""
    q = request.get_form_var('q')
    repos = CodeDoubanProject.search_by_name(name=q, limit=7)
    data = {
        'repos': [{'name': repo.name,
                   'owner_name': repo.owner_name,
                   'owner_avatar': User(repo.owner_id).avatar_url,
                   'url': repo.url} for repo in repos]
    }
    return json.dumps(data)


def autocomplete_users(request):
    q = request.get_form_var('q')
    users = CodeDoubanProject.search_for_owners(name=q, limit=7)
    data = {'users': [{'name': user, 'avatar': User(user).avatar_url,
                       'url': User(user).url} for user in users]}
    return json.dumps(data)


def get_code_version(request):
    # TODO
    return json.dumps({'code_version': 'unknow',
                       'release_time': 'unknow'
                       })


def card_info(request):
    user_or_team_id = request.get_form_var('user')
    team = Team.get_by_uid(user_or_team_id)
    user_existed = User.check_exist(user_or_team_id)
    if not team or user_existed:
        user = User(user_or_team_id)
        data = {
            'user': {'name': user_or_team_id, 'avatar': user.avatar_url,
                     'url': user.url,
                     'badges': [{'img': item.badge.get_image_url(),
                                 'name': item.badge.name,
                                 'reason': item.reason or item.badge.summary}
                                for item in user.get_badge_items()]}
        }
    else:
        members = team.user_ids[::-1]  # 根据团队的时间排序
        displayed_users = [User(uid) for uid in team.user_ids[:8]]
        data = {
            'team': {
                'id': team.uid,
                'name': team.name,
                'url': team.url,
                'desc': team.short_description,
                'profile_url': team.profile_url(),
                'members': [{'uid': u.name, 'avatar_url': u.avatar_url}
                            for u in displayed_users],
                'member_count': len(members)
            }
        }
    return json.dumps(data)


class RawUI:
    _q_exports = ['/']

    def __init__(self, request, proj_name, filepath_parts=[]):
        self.proj_name = proj_name
        self.filepath_parts = filepath_parts

    def __call__(self, request):
        proj = CodeDoubanProject.get_by_name(self.proj_name)
        ref = request.get_form_var('rev', 'HEAD')
        filename = '/'.join(self.filepath_parts)
        # TODO: check ref
        ret = proj.repo.get_file(ref, filename.decode('utf-8'))
        if ret is None:
            raise TraversalError()
        return str(ret.data.encode('utf8'))

    def _q_lookup(self, request, filename):
        return RawUI(request, self.proj_name, self.filepath_parts + [filename])


# TODO: move to api.py or repos.py
# FIXME: unify the project checking.
class APIUI:
    _q_exports = ['hooks', 'commits', 'meta', 'src', 'commits_by_path',
                  'git', 'issues', 'issue', 'raw', 'pulls', 'pull',
                  'statuses', 'timeline', 'files', 'diff']

    def __init__(self, request, proj_name):
        proj_name = self.get_project_name(proj_name)
        self.proj_name = proj_name
        project = CodeDoubanProject.get_by_name(proj_name)
        self.project = project
        if project:
            self.raw = RawUI(request, project.name)
            self.issues = IssuesUI(request, project.name)
            self.issue = IssueUI(request, project.name)
            self.pulls = PullsUI(request, project.name)
            self.diff = PullDiffUI(request, project.name)
            self.pull = PullUI(request, project.name)
            self.commits = CommitsUI(request, project)
            self.statuses = StatusesUI(request, project)
            self.files = FilesUI(request, project)
            self.git = GitUI(self.project)

    def _q_index(self, request):
        if self.project:
            return self._project_json(request)
        else:
            raise api_errors.NotFoundError('repo')

    @jsonize
    def _project_json(self, request):
        dic = self.project.as_dict()
        dic['readme'] = self.project.readme
        return dic

    def hooks(self, request):
        if not self.project:
            raise api_errors.NotFoundError("project")
        data = map((lambda x: x.__dict__), self.project.hooks)
        return json.dumps(data)

    def meta(self, request):
        if not self.project:
            raise api_errors.NotFoundError("project")
        data = self.project.get_info()
        request.response.set_content_type('application/json; charset=utf8')
        return json.dumps(data)

    def src(self, request):
        if not self.project:
            raise api_errors.NotFoundError("project")
        ''' e.g. /api/testuser/testproj/src?path=test.md&ref=5c712b6712bec9c4ed1531b61fd7a4cbcbf3fe90 '''  # noqa
        path = request.get_form_var('path')
        ref = request.get_form_var('ref') or 'HEAD'
        t, src = '', ''
        _ref = ':'.join((ref, path or ''))
        try:
            # file_content = src.data
            src = self.project.repo.get_path_by_ref(_ref)
            if not src:
                raise ValueError
            t = src.type
            if t == 'blob':
                if src.binary:
                    if path.endswith('.pdf'):
                        src = '<a class="media" href="%s"></a>' % (
                            '/' + self.project.name + '/raw/' + ref + '/' + path)
                    else:
                        src = '<div class="rawfile">The content of %s appear to be raw binary, please use raw view instead</div>' % path  # noqa
                elif path.endswith(('md', 'mkd', 'markdown')):
                    src = '<div class="markdown-body">{}</div>'.format(
                        format_md_or_rst(path, src.data, self.project.name))
                else:
                    src = highlight_code(path, src.data, div=True)
            elif t == 'tree':
                src = [dict(e) for e in src]
        except (KeyError, ValueError):
            t = 'blob'
            src = '<div class="error"><i class="icon-exclamation-sign"></i> File not found.</div>'  # noqa
        data = {'path': path, 'type': t, 'src': src}
        return json.dumps(data)

    def commits_by_path(self, request):
        if not self.project:
            raise api_errors.NotFoundError("project")
        path = request.get_form_var('path', '')
        ref = request.get_form_var('ref') or 'HEAD'
        commits = {'r': 1}
        cs = {}
        try:
            tree = self.project.repo.get_tree(ref, path=path, with_commit=True)
            for v in tree:
                k = v['id']
                v['message_with_emoji'] = parse_emoji(
                    escape(v['commit']['message']))
                author = get_author_by_email(
                    v['commit']['author']['email'])
                if author:
                    v['contributor'] = author
                    v['contributor_url'] = "%s/people/%s" % (DOMAIN, author)
                else:
                    v['contributor'] = v['commit']['author']['name']
                v['age'] = compute_relative_time(v['commit']['author']['time'])
                v['sha'] = v['commit']['sha']
                v['commit_id'] = v['commit']['sha']
                cs[k] = v
            commits['commits'] = cs
        except KeyError:
            commits = {'r': '0', 'err': 'Path not found'}
        except IOError:
            commits = {'r': '0', 'err': 'Path not found'}
        return json.dumps(commits)

    def _q_lookup(self, request, name):
        proj_name = "%s/%s" % (self.proj_name, name)
        proj_name = self.get_project_name(proj_name)
        if CodeDoubanProject.exists(proj_name):
            return APIUI(request, proj_name)

    def get_project_name(self, name):
        if name and name.endswith('.git'):
            return name[:-4]
        return name


def timeline(request):
    from vilya.models.timeline import format_timeline
    from vilya.models.feed import get_public_feed
    timestamp = request.get_form_var('timestamp')
    count = request.get_form_var('count') or 15
    start = request.get_form_var('start') or 0
    start = int(start)
    count = int(count)
    if timestamp:
        actions = get_public_feed().get_actions_by_timestamp(max=timestamp)
        actions = actions[:count]
    else:
        actions = get_public_feed().get_actions(start, start + count)
    data = []
    for action in actions:
        formated_action = format_timeline(action)
        if formated_action:
            data.append(formated_action)
    return json.dumps(data)


@apply
class svn2git(object):
    _q_exports = []

    def _q_index(self, request):
        rev = request.get_form_var('rev')
        if rev and rev.isdigit():
            return self._q_lookup(request, rev)
        raise TraversalError

    def _q_lookup(self, request, rev):
        name = 'shire_git_RO'
        project = CodeDoubanProject.get_by_name(name)
        repo = project.repo
        query = 'trunk@' if rev == 'HEAD' else "trunk@%s " % rev
        commits = repo.get_commits("HEAD",
                                   query=query,
                                   max_count=1)
        commit = commits[0] if commits else None
        if commit:
            return request.redirect(commit.url)


def _q_exception_handler(request, exception):
    # return Not Found instead of TraversalError in api
    if isinstance(exception, TraversalError):
        exception = api_errors.NotFoundError()

    if not isinstance(exception, (OAuthError, CodeAPIError)):
        raise exception

    if isinstance(exception, CodeAPIError):
        error_data = exception.to_dict()
    else:
        error_data = dict(
            code=exception.status_code,
            msg=exception.message,
            request='%s: %s' % (request.method, request.url)
        )
    request.response.set_content_type('application/json; charset=utf-8')
    return json.dumps(error_data)
