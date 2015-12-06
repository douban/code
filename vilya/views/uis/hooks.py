# -*- coding: utf-8 -*-

from __future__ import absolute_import

from vilya.libs.template import st

from vilya.models.project import CodeDoubanProject
from vilya.models.hook import CodeDoubanHook
from vilya.models.consts import FEATURE_HOOK_URLS, TELCHAR_URL

_q_exports = []


class HookUI:
    _q_exports = ['new']

    def __init__(self, proj_name):
        self.proj_name = proj_name

    def _q_index(self, request):
        errors = ''
        project_name = self.proj_name
        user = request.user
        project = CodeDoubanProject.get_by_name(project_name)
        hooks = [hook for hook in project.hooks
                 if hook.url not in FEATURE_HOOK_URLS]
        enabled_telchar = next((hook for hook in project.hooks
                               if hook.url == TELCHAR_URL), False)
        return st('settings/hooks.html', **locals())

    def new(self, request):
        errors = ''
        project_name = self.proj_name
        user = request.user
        url = request.get_form_var('url')
        project = CodeDoubanProject.get_by_name(project_name)
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
                return request.redirect('/%s/settings/hooks' % project_name)

        return st('settings/hooks.html', **locals())

    def _q_lookup(self, request, hook_id):
        project_name = self.proj_name
        user = request.user
        project = CodeDoubanProject.get_by_name(project_name)
        if request.get_form_var('_method') == 'delete' \
           and project.is_owner(user):
            hooks = project.hooks
            hook = (h for h in hooks if int(h.id) == int(hook_id)).next()
            hook.destroy()
        return request.redirect('/%s/settings/hooks' % project_name)
