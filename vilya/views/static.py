# -*- coding: utf-8 -*-

from __future__ import absolute_import
from vilya.static import get_static


class StaticUI():
    _q_exports = []

    def __init__(self, request, path=''):
        self.path = path

    def _q_lookup(self, request, name):
        return StaticUI(request, '%s/%s' % (self.path, name))

    def __call__(self, request):
        if self.path.endswith('.js'):
            request.response.set_content_type('application/x-javascript')
        elif self.path.endswith('.css'):
            request.response.set_content_type('text/css')

        r = get_static('/' + self.path)
        return r
