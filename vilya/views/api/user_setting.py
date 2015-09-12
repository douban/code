# -*- coding: utf-8 -*-
from vilya.libs.template import st

_q_exports = []


def _q_lookup(request, part):
    if part == 'css':
        return CustomCssUI(request)


class CustomCssUI(object):
    _q_exports = []
    _q_methods = ['get']

    def __init__(self, request):
        self.user = request.user

    def _q_index(self, request):
        user = self.user
        return st('/widgets/custom_css.html', **locals())

    def _q_access(self, request):
        request.response.set_content_type('text/css')
