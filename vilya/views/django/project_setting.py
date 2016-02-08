# -*- coding: utf-8 -*-

from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from vilya.libs.template import st


@csrf_exempt
def index(request, username, projectname):
    from vilya.models.team import Team
    from vilya.models.project import CodeDoubanProject
    from vilya.models.user import User
    name = '/'.join([username, projectname])
    project = CodeDoubanProject.get_by_name(name)
    user = request.user
    if not project:
        raise Http404
    if not project.is_owner(request.user):
        return HttpResponseForbidden()

    if request.method == 'GET':
        teams = Team.gets()
        owner = User(project.owner_id)
        committers = project.get_committers_by_project(project.id)

        if project.fork_from:
            fork_from = CodeDoubanProject.get(project.fork_from)

        return HttpResponse(st('settings/main.html', **locals()))

    elif request.method == 'POST':
        if user.name == project.owner_id:
            summary = request.POST.get('summary', '')
            product = request.POST.get('product', '')
            intern_banned = request.POST.get('intern_banned', None)
            project.update(summary, product, name, intern_banned)

        return HttpResponseRedirect('/%s/settings' % name)


def add_committer(request, username, projectname):
    from vilya.models.project import CodeDoubanProject
    name = '/'.join([username, projectname])
    project = CodeDoubanProject.get_by_name(name)
    user = request.user
    if request.method == 'POST':
        if user.name == project.owner_id:
            committers = request.POST.get('username', '')
            committers = committers.split(' ')
            for committer in committers:
                project.add_committer(project.id, committer)
    return HttpResponseRedirect('/%s/settings' % name)


def del_committer(request, username, projectname):
    from vilya.models.project import CodeDoubanProject
    name = '/'.join([username, projectname])
    project = CodeDoubanProject.get_by_name(name)
    user = request.user
    if request.method == 'POST':
        if user.name == project.owner_id:
            committers = request.POST.get('username', '')
            project.del_committer(project.id, committers)
    return HttpResponseRedirect('/%s/settings' % name)


def sphinx_docs(request, username, projectname):
    from tasks import sphinx_builds_add
    from vilya.models.sphinx_docs import SphinxDocs
    from vilya.models.project import CodeDoubanProject
    name = '/'.join([username, projectname])
    project = CodeDoubanProject.get_by_name(name)
    user = request.user
    docs = SphinxDocs(name)
    if request.GET.get('force_rebuild') == 'mq':
        sphinx_builds_add(name)
        return HttpResponseRedirect('/%s/settings/sphinx_docs' % name)
    if request.GET.get('force_rebuild') == 'direct':
        docs.build_all()
        return HttpResponseRedirect('/%s/settings/sphinx_docs' % name)
    tdt = {
        'project': project,
        'request': request,
        'enabled': docs.enabled,
        'last_build': docs.last_build_info(),
        'user': user,
    }
    return HttpResponse(st('settings/sphinx_docs.html', **tdt))


def hooks_index(request, username, projectname):
    # FIXME(xutao) remove TELCHAR_URL
    from vilya.models.consts import FEATURE_HOOK_URLS, TELCHAR_URL
    from vilya.models.project import CodeDoubanProject
    name = '/'.join([username, projectname])
    errors = ''
    user = request.user
    project = CodeDoubanProject.get_by_name(name)
    hooks = [hook for hook in project.hooks
             if hook.url not in FEATURE_HOOK_URLS]
    enabled_telchar = next((hook for hook in project.hooks
                            if hook.url == TELCHAR_URL), False)
    return HttpResponse(st('settings/hooks.html', **locals()))


@csrf_exempt
def hooks_new(request, username, projectname):
    from vilya.models.hook import CodeDoubanHook
    from vilya.models.project import CodeDoubanProject
    name = '/'.join([username, projectname])
    errors = ''
    user = request.user
    url = request.get_form_var('url')
    project = CodeDoubanProject.get_by_name(name)
    hooks = project.hooks
    if request.method == "POST":
        hook = CodeDoubanHook(0, url, project.id)
        exists_id = CodeDoubanHook.get_id_by_url(project.id, url)
        errors = hook.validate()
        if not project.is_owner(user):
            errors.append("You can't set hooks for this project")
        if exists_id is not None:
            errors.append("This hook url has exists")
        if not errors:
            CodeDoubanHook.add(hook.url, hook.project_id)
            return HttpResponseRedirect('/%s/settings/hooks' % name)
    return HttpResponse(st('settings/hooks.html', **locals()))


def hooks_hook(request, username, projectname, id):
    from vilya.models.project import CodeDoubanProject
    name = '/'.join([username, projectname])
    user = request.user
    hook_id = id
    project = CodeDoubanProject.get_by_name(name)
    if request.get_form_var('_method') == 'delete' \
        and project.is_owner(user):
        hooks = project.hooks
        hook = (h for h in hooks if int(h.id) == int(hook_id)).next()
        hook.destroy()
    return HttpResponseRedirect('/%s/settings/hooks' % name)


def conf(request, username, projectname):
    from vilya.models.project import CodeDoubanProject
    name = '/'.join([username, projectname])
    project = CodeDoubanProject.get_by_name(name)
    user = request.user
    tdt = {
        'user': user,
        'project': project,
        'request': request,
    }
    return HttpResponse(st('settings/config.html', **tdt))


def pages(request, username, projectname):
    from vilya.models.sphinx_docs import SphinxDocs
    from vilya.models.project import CodeDoubanProject
    name = '/'.join([username, projectname])
    user = request.user
    project = CodeDoubanProject.get_by_name(name)
    docs = SphinxDocs(name)
    tdt = {
        'project': project,
        'request': request,
        'user': user,
        'docs': docs,
        'last_build': docs.last_build_info(),
    }
    return HttpResponse(st('settings/pages.html', **tdt))


def transfer_project(request, username, projectname):
    from vilya.models.project import CodeDoubanProject
    name = '/'.join([username, projectname])
    project = CodeDoubanProject.get_by_name(name)
    user_id = request.GET.get('username')
    if user_id:
        project.transfer_to(user_id)
        return HttpResponse('transfer success')
    return HttpResponse('please input a username')


def rename_project(request, username, projectname):
    from vilya.models.project import CodeDoubanProject
    name = '/'.join([username, projectname])
    project = CodeDoubanProject.get_by_name(name)
    repo_name = request.GET.get('repo_name')
    if repo_name:
        if project.rename(repo_name) is not False:
            return HttpResponseRedirect(project.url)
        else:
            return HttpResponse("repo name already exist")
    return HttpResponse('please input a repo name')


def groups_index(request, username, projectname):
    from vilya.models.team import Team
    from vilya.models.team_group import TeamGroup
    from vilya.models.project import CodeDoubanProject
    name = '/'.join([username, projectname])
    project = CodeDoubanProject.get_by_name(name)
    group_name = request.GET.get('group', '')
    if not group_name:
        return HttpResponseRedirect("%ssettings/" % project.url)
    team, _, group = group_name.rpartition('/')
    t = Team.get_by_uid(team)
    if not t:
        return HttpResponseRedirect("%ssettings/" % project.url)
    g = TeamGroup.get(team_id=t.id, name=group)
    if not g:
        return HttpResponseRedirect("%ssettings/" % project.url)
    g.add_project(project_id=project.id)
    return HttpResponseRedirect("%ssettings/" % project.url)


def groups_destory(request, username, projectname):
    from vilya.models.team import Team
    from vilya.models.team_group import TeamGroup
    from vilya.models.project import CodeDoubanProject
    name = '/'.join([username, projectname])
    project = CodeDoubanProject.get_by_name(name)
    group_name = request.GET.get('group', '')
    if not group_name:
        return HttpResponseRedirect("%ssettings/" % project.url)
    team, _, group = group_name.rpartition('/')
    t = Team.get_by_uid(team)
    if not t:
        return HttpResponseRedirect("%ssettings/" % project.url)
    g = TeamGroup.get(team_id=t.id, name=group)
    if not g:
        return HttpResponseRedirect("%ssettings/" % project.url)
    g.remove_project(project_id=project.id)
    return HttpResponseRedirect("%ssettings/" % project.url)
