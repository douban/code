# -*- coding: utf-8 -*-

from __future__ import absolute_import
import re
from datetime import datetime

from vilya.libs.template import st
from vilya.libs.signals import team_created_signal
from vilya.models.project import CodeDoubanProject
from vilya.models.mirror import CodeDoubanMirror
from vilya.models.team import Team
from vilya.models.user import User
from vilya.models.consts import (
    ORGANIZATION_PROJECT, TEAM_OWNER, MIRROR_PROJECT,
    PEOPLE_PROJECT, MIRROR_STATE_CLONING, MIRROR_NOT_PROXY)
from vilya.models.feed import (
    get_public_feed, get_user_feed, PAGE_ACTIONS_COUNT)
from vilya.views.hub.search_beta import SearchUI
from vilya.views.teams import TeamsUI

_q_exports = ['teams', 'create', 'future', 'notification', 'my_pull_requests',
              'remove', 'watch', 'unwatch', 'yours', 'my_issues',
              'public_timeline', 'search', 'emoji', 'bo', 'team',
              'add_team', 'beacon', 'shop', 'stat', 'chat', 'center']


def bo(request):
    return request.redirect('/shire_git_RO/commits/master/?author=bo')


def teams(request):
    return TeamsUI()._q_index(request)


def emoji(request):
    return st('emoji.html', **locals())


def public_timeline(request):
    actions = get_public_feed().get_actions(stop=PAGE_ACTIONS_COUNT - 1)
    return st('public_timeline.html', **locals())


def yours(request):
    user = request.user
    actions = (get_user_feed(user.username)
               .get_actions(stop=PAGE_ACTIONS_COUNT - 1))

    your_projects = CodeDoubanProject.get_projects(
        owner=user.username, sortby="lru")
    watched_projects = CodeDoubanProject.get_watched_others_projects_by_user(
        user=user.username, sortby='lru')

    badge_items = user.get_badge_items()
    return st('my_actions.html', **locals())


def search(request):
    q = request.get_form_var('q')
    if q:
        results = CodeDoubanProject.search_by_name(q)
    return st('search.html', **locals())


def create(request):
    user = request.user
    if not user:
        return request.redirect("/")
    errors = ""

    template_filename = 'create.html'

    if request.method == "POST":
        name = request.get_form_var('name')
        product = request.get_form_var('product')
        org_proj = request.get_form_var('org_proj')
        summary = request.get_form_var('summary')
        repo_url = request.get_form_var('url')
        fork_from = request.get_form_var('fork_from')
        intern_banned = request.get_form_var('intern_banned', None)
        with_proxy = request.get_form_var('with_proxy', MIRROR_NOT_PROXY)
        with_proxy = int(with_proxy)
        mirror = None

        def add_people_project(project):
            name = "%s/%s" % (project.owner_id, project.name)
            _project = CodeDoubanProject.add(
                name=name, owner_id=project.owner_id,
                summary=project.summary, product=project.product,
                intern_banned=project.intern_banned)
            return _project

        def add_org_project(project):
            _project = CodeDoubanProject.add(
                name=name, owner_id=project.owner_id,
                summary=project.summary, product=project.product,
                intern_banned=project.intern_banned)
            return _project

        def add_mirror_project(project):
            name = "mirror/%s" % (project.name)
            _project = CodeDoubanProject.add(
                name=name, owner_id='mirror', summary=project.summary,
                product=project.product, intern_banned=project.intern_banned,
                mirror=project.mirror_url)
            if _project:
                CodeDoubanMirror.add(url=project.mirror_url,
                                     state=MIRROR_STATE_CLONING,
                                     project_id=_project.id,
                                     with_proxy=project.mirror_proxy)
            return _project

        def add_fork_project(project):
            name = "%s/%s" % (project.owner_id, project.name)
            _project = CodeDoubanProject.add(
                name=name, owner_id=project.owner_id, summary=project.summary,
                product=project.product, fork_from=project.fork_from,
                intern_banned=project.intern_banned)
            if _project:
                fork_from_project = CodeDoubanProject.get(project.fork_from)
                _project.update(project.summary,
                                project.product,
                                name,
                                fork_from_project.intern_banned)
            return _project

        def validate_project(project_type, project):
            error = ''
            if project_type in (PEOPLE_PROJECT, ORGANIZATION_PROJECT):
                error = project.validate()
            elif project_type == MIRROR_PROJECT:
                error = project.validate()
                if not error:
                    error = CodeDoubanMirror.validate(project.mirror_url)
            else:
                error = project.validate()
            return error

        def add_project(project):
            _project = None
            if project_type == PEOPLE_PROJECT:
                _project = add_people_project(project)
            elif project_type == ORGANIZATION_PROJECT:
                _project = add_org_project(project)
            elif project_type == MIRROR_PROJECT:
                _project = add_mirror_project(project)
            else:
                _project = add_fork_project(project)
            return _project

        project = CodeDoubanProject(None, name, user.username, summary,
                                    datetime.now(), product, None, None,
                                    fork_from=fork_from,
                                    intern_banned=intern_banned,
                                    mirror_url=repo_url,
                                    mirror_proxy=with_proxy)
        # FIXME: rename org_proj of html
        project_type = org_proj
        errors = validate_project(project_type, project)
        if errors:
            return st(template_filename, **locals())

        project = add_project(project)
        if not project:
            fork_from = ''
            errors = 'project exists'
            return st(template_filename, **locals())

        CodeDoubanProject.add_watch(project.id, user.name)
        return request.redirect('/%s/' % project.name)

    fork_from = ''
    if request.get_form_var('fork_from'):
        fork_from = CodeDoubanProject.get(request.get_form_var('fork_from'))
        name = "%s/%s" % (user.name, fork_from.realname)
        if CodeDoubanProject.exists(name):
            return request.redirect('/%s/' % name)
        projects = CodeDoubanProject.gets_by_owner_id(user.name)
        for p in projects:
            if p.origin_project_id == fork_from.id and '/' in p.name:
                return request.redirect('/%s/' % p.name)
    return st(template_filename, **locals())


def future(request):
    return st('future.html', **locals())


def check_project(name):
    namere = re.compile(r'\w+')
    if len(name) > 100:
        return "error"
    if not namere.match(name):
        return "error"


def watch(request):
    user = request.user
    if not user:
        return request.redirect("/")
    errors = ""
    if request.method == "POST":
        proj_id = request.get_form_var('proj_id')
        CodeDoubanProject.add_watch(proj_id, user.name)
        project = CodeDoubanProject.get(proj_id)
        return request.redirect('/%s/' % project.name)

    proj_id = request.get_form_var('proj_id') or ""
    project = CodeDoubanProject.get(proj_id)
    action = "watch"
    return st('watch.html', **locals())


def unwatch(request):
    user = request.user
    if not user:
        return request.redirect("/")
    errors = ""
    if request.method == "POST":
        proj_id = request.get_form_var('proj_id')
        CodeDoubanProject.del_watch(proj_id, user.name)
        project = CodeDoubanProject.get(proj_id)
        return request.redirect('/%s/' % project.name)

    proj_id = request.get_form_var('proj_id') or ""
    project = CodeDoubanProject.get(proj_id)
    action = "unwatch"
    return st('watch.html', **locals())


def add_team(request):
    user = request.user
    if not user:
        return request.redirect("/")

    uid = request.get_form_var('uid') or ''
    name = request.get_form_var('name') or ''
    description = request.get_form_var('description') or ''

    errors = ""
    if request.method == "POST":
        teams = Team.gets()
        team_uid_pattern = re.compile(r'[a-zA-Z0-9\_]*')
        if not uid:
            error = 'uid_not_exists'
        elif not name:
            error = 'name_not_exists'
        elif uid != re.findall(team_uid_pattern, uid)[0]:
            error = 'invilid_uid'
        elif uid in [team.uid for team in teams]:
            error = 'uid_existed'
        elif User.check_exist(uid):
            error = 'user_id_existed'
        elif name in [team.name for team in teams]:
            error = 'name_existed'
        else:
            team = Team.add(uid, name, description)
            if team:
                team_created_signal.send(user.name,
                                         team_name=team.name,
                                         team_uid=team.uid)
                team.add_user(user, TEAM_OWNER)
                return request.redirect(team.url)

    return st('/teams/add_team.html', **locals())


def _q_lookup(request, url_part):
    if url_part == 'search_beta':
        return SearchUI()
