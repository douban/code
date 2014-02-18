# -*- coding: utf-8 -*-

from __future__ import absolute_import
from quixote.errors import TraversalError, AccessError
from vilya.libs.template import st
from vilya.models.organization import Organization

_q_exports = []


def __call__(request):
    return _q_index(request)


def _q_index(request):
    context = {}
    return st('organizations/new.html', **context)
