# -*- coding: utf-8 -*-

from __future__ import absolute_import
from vilya.libs.template import st

_q_exports = []


def __call__(request):
    return _q_index(request)


def _q_index(request):
    context = {}
    return st('organizations/new.html', **context)
