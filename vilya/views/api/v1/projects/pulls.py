# -*- coding: utf-8 -*-

from __future__ import absolute_import
from vilya.models.user import User
from vilya.models.card import Card
from vilya.models.pull import Pull
from vilya.views.api.errors import (NotFoundError,
                                    UnprocessableEntityError,
                                    MissingFieldError,
                                    ForbiddenError,
                                    InvalidFieldError)
from vilya.views.api.utils import RestAPIUI

PULLS_PER_PAGE = 35


class PullsUI(RestAPIUI):
    _q_exports = []
    _q_methods = ['get', 'post']

    def __init__(self, project):
        self.project = project

    def get(self, request):
        pulls = Pull.gets(upstream_project_id=self.project.id)
        return [p.to_dict() for p in pulls]

    def post(self, request):
        user = request.user
        name = request.data.get('name')
        issue = request.data.get('issue')
        head = request.data.get('head')
        base = request.data.get('base')
        description = request.data.get('description')
        if not name:
            raise MissingFieldError('name')
        upstream = self.project
        origin_user = user
        if ':' in head:
            username, _, branch = head.partition(':')
            origin_user = User.get(name=username)
        origin = upstream.forked(origin_user)
        if not origin:
            raise InvalidFieldError('head')
        if not origin.can_push(user):
            raise ForbiddenError
        pull = Pull.open(origin.id,
                         head,
                         upstream.id,
                         base or upstream.repo.default_branch)
        if not pull.is_validated:
            raise UnprocessableEntityError
        p = upstream.create_pull(name=name,
                                 description=description,
                                 origin_project_id=pull.origin_project_id,
                                 origin_project_ref=pull.origin_project_ref,
                                 upstream_project_id=pull.upstream_project_id,
                                 upstream_project_ref=pull.upstream_project_ref,
                                 creator_id=user.id)
        if not p:
            raise UnprocessableEntityError
        return p.to_dict()

    def _q_lookup(self, request, part):
        card = Card.get(project_id=self.project.id,
                        number=int(part))
        if not card:
            raise NotFoundError('pull %s', part)
        if not card.pull:
            raise NotFoundError('pull %s', part)
        return PullUI(card)


class PullUI(RestAPIUI):
    _q_exports = []
    _q_methods = ['get']

    def __init__(self, card):
        self.card = card

    def get(self, request):
        return {}
