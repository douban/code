# -*- coding: utf-8 -*-

from __future__ import absolute_import
from quixote.errors import TraversalError, AccessError
from vilya.libs.template import st
from vilya.models.organization import Organization

_q_exports = ['new']


def __call__(request):
    return _q_index(request)


def _q_index(request):
    context = {}
    if request.method == "POST":
        name = request.get_form_var('name')
        description = request.get_form_var('description')
        creator_id = int(request.get_form_var('creator_id', 1))
        o = Organization.create(name=name,
                             description=description,
                             owner_id=creator_id,
                             creator_id=creator_id)
        if o:
            return request.redirect('organizations/%s' % o.name)
        context['organization'] = o
        return st('organizations/index.html', **context)
    organizations = Organization.gets_by()
    context['organizations'] = organizations
    return st('organizations/index.html', **context)


def _q_lookup(request, part):
    o = Organization.get(name=part)
    if o:
        return OrganizationUI(o)
    raise TraversalError


class OrganizationUI(object):
    _q_exports = []

    def __init__(self, organization):
        self.organization = organization

    def __call__(self, request):
        return self._q_index(request)

    def _q_index(self, request):
        context = {}
        context['organization'] = self.organization
        return st('organizations/org.html', **context)

    def _q_lookup(self, request, part):
        raise TraversalError
