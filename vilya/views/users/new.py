# -*- coding: utf-8 -*-

from __future__ import absolute_import
from quixote.errors import TraversalError, AccessError
from vilya.libs.template import st

_q_exports = []


def __call__(request):
    return _q_index(request)


def _q_index(request):
    return st('users/new.html')
