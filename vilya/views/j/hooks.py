# coding=utf-8
from vilya.views.util import jsonize
from quixote.errors import TraversalError

from vilya.models.project import CodeDoubanProject
from vilya.models.hook import CodeDoubanHook
from vilya.models.consts import TELCHAR_URL

_q_exports = []


def _q_lookup(request, proj_id):
    if proj_id.isdigit():
        return JHookUI(proj_id)
    raise TraversalError


class JHookUI(object):
    _q_exports = ['telchar']

    def __init__(self, proj_id):
        self.proj_id = proj_id

    @jsonize
    def telchar(self, request):
        proj_id = self.proj_id
        user = request.user
        project = CodeDoubanProject.get(proj_id)
        url = TELCHAR_URL

        if project.is_owner(user):
            is_disable = request.get_form_var('close', '')
            if is_disable:
                hook = CodeDoubanHook.get_by_url(url)
                if hook:
                    hook.destroy()
                status = 0
            else:
                CodeDoubanHook.add(url, proj_id)
                status = 1
            return {'r': 0, 'status': status}
        return {'r': 1}
