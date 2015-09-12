# -*- coding: utf-8 -*-

from __future__ import absolute_import
from quixote.errors import AccessError, TraversalError
from vilya.libs.template import st
from vilya.models.user import User
from vilya.models.project import CodeDoubanProject
from vilya.models.sphinx_docs import SphinxDocs
from vilya.models.team import Team
from vilya.models.team_group import TeamGroup
from tasks import sphinx_builds_add
from vilya.views.uis.hooks import HookUI
from vilya.views.uis.conf import SettingsConfUI


_q_exports = []


class SettingsUI(object):

    _q_exports = ['add_committer', 'del_committer', 'sphinx_docs', 'hooks',
                  'conf', 'pages', 'transfer_project', 'rename_project',
                  'groups']

    def __init__(self, proj_name):
        self.proj_name = proj_name
        self.project = CodeDoubanProject.get_by_name(self.proj_name)
        if not self.project:
            raise TraversalError

    def _q_access(self, request):
        self.user = request.user
        if not self.project.is_owner(self.user):
            raise AccessError

    def _q_index(self, request):
        user = request.user
        project = self.project

        if request.method == 'GET':
            teams = Team.gets()
            owner = User(self.project.owner_id)
            committers = project.get_committers_by_project(project.id)

            if project.fork_from:
                fork_from = CodeDoubanProject.get(project.fork_from)

            return st('settings/main.html', **locals())

        elif request.method == 'POST':
            if user.name == project.owner_id:
                summary = request.get_form_var('summary', '')
                product = request.get_form_var('product', '')
                intern_banned = request.get_form_var('intern_banned', None)
                project.update(summary, product, self.proj_name, intern_banned)

            return request.redirect('/%s/settings' % self.proj_name)

    def committer(self, request, action):
        user = request.user
        project = self.project

        if request.method == 'POST':
            if user.name == project.owner_id:
                committers = request.get_form_var('username', '')
                if action == 'add':
                    committers = committers.split(' ')
                    for committer in committers:
                        project.add_committer(project.id, committer)
                elif action == 'del':
                    project.del_committer(project.id, committers)

    def add_committer(self, request):
        self.committer(request, 'add')
        return request.redirect('/%s/settings' % self.proj_name)

    def del_committer(self, request):
        self.committer(request, 'del')
        return request.redirect('/%s/settings' % self.proj_name)

    def sphinx_docs(self, request):
        user = request.user
        docs = SphinxDocs(self.proj_name)
        if request.get_form_var('force_rebuild') == 'mq':
            sphinx_builds_add(self.proj_name)
            return request.redirect(
                '/%s/settings/sphinx_docs' % self.proj_name)
        if request.get_form_var('force_rebuild') == 'direct':
            docs.build_all()
            return request.redirect(
                '/%s/settings/sphinx_docs' % self.proj_name)
        tdt = {
            'project': CodeDoubanProject.get_by_name(self.proj_name),
            'request': request,
            'enabled': docs.enabled,
            'last_build': docs.last_build_info(),
            'user': user,
        }
        return st('settings/sphinx_docs.html', **tdt)

    @property
    def hooks(self):
        return HookUI(self.proj_name)

    @property
    def conf(self):
        return SettingsConfUI(self.proj_name)

    def pages(self, request):
        user = request.user
        docs = SphinxDocs(self.proj_name)
        tdt = {
            'project': CodeDoubanProject.get_by_name(self.proj_name),
            'request': request,
            'user': user,
            'docs': docs,
            'last_build': docs.last_build_info(),
        }
        return st('settings/pages.html', **tdt)

    def transfer_project(self, request):
        user_id = request.get_form_var('username')
        if user_id:
            self.project.transfer_to(user_id)
            return 'transfer success'
        return 'please input a username'

    def rename_project(self, request):
        repo_name = request.get_form_var('repo_name')
        if repo_name:
            if self.project.rename(repo_name) is not False:
                return request.redirect(self.project.url)
            else:
                return "repo name already exist"
        return 'please input a repo name'

    @property
    def groups(self):
        return SettingsGroupsUI(self.project)


class SettingsGroupsUI(object):
    _q_exports = ['destroy']

    def __init__(self, project):
        self.project = project

    def _q_index(self, request):
        project = self.project
        group_name = request.get_form_var('group', '')
        if not group_name:
            return request.redirect("%ssettings/" % project.url)
        team, _, group = group_name.rpartition('/')
        t = Team.get_by_uid(team)
        if not t:
            return request.redirect("%ssettings/" % project.url)
        g = TeamGroup.get(team_id=t.id, name=group)
        if not g:
            return request.redirect("%ssettings/" % project.url)
        g.add_project(project_id=project.id)
        return request.redirect("%ssettings/" % project.url)

    def destroy(self, request):
        project = self.project
        group_name = request.get_form_var('group', '')
        if not group_name:
            return request.redirect("%ssettings/" % project.url)
        team, _, group = group_name.rpartition('/')
        t = Team.get_by_uid(team)
        if not t:
            return request.redirect("%ssettings/" % project.url)
        g = TeamGroup.get(team_id=t.id, name=group)
        if not g:
            return request.redirect("%ssettings/" % project.url)
        g.remove_project(project_id=project.id)
        return request.redirect("%ssettings/" % project.url)
