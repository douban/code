# -*- coding: utf-8 -*-

from vilya.views.api import v1

_q_exports = []

VERSIONS = {'v1': v1, }
DEFAULT_VERSION = v1


def _q_access(request):
    request.response.set_content_type('application/json; charset=utf8')


def _q_lookup(request, part):
    if not part:
        return DEFAULT_VERSION.APIRoot()

    version = VERSIONS.get(part)
    if version:
        return version.APIRoot()
    else:
        root = DEFAULT_VERSION.APIRoot()
        return root.publish(request, part)
