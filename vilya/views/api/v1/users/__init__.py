# -*- coding: utf-8 -*-

from __future__ import absolute_import
from quixote.errors import TraversalError
from vilya.views.api.utils import json_body, jsonize, http_status
from vilya.models.user import User
from vilya.views.api.utils import RestAPIUI


class UsersUI(RestAPIUI):
    _q_exports = []
    _q_methods = ['get', 'post']

    def get(self, request):
        return []

    @jsonize
    @json_body
    @http_status(201)
    def _post(self, request):
        return self.post(request)

    def post(self, request):
        name = request.data.get('name')
        password = request.data.get('password')
        description = request.data.get('description', '')
        email = request.data.get('email', '')
        new_user = User.create(name=name,
                               password=password,
                               description=description,
                               email=email)
        if new_user:
            new_user.set_session(request)
            return new_user.to_dict()
        else:
            return {}

    def _q_lookup(self, request, name):
        user = User.get(name=name)
        if user:
            return UserUI(user)
        raise TraversalError


class UserUI(RestAPIUI):
    _q_methods = ['get']

    def __init__(self, user=None):
        self.user = user

    def get(self, request):
        user = self.user
        if not user:
            return {}
        return user.to_dict()


class CurrentUserUI(RestAPIUI):
    _q_exports = []
    _q_methods = ['get', 'post']

    def get(self, request):
        user = request.user
        if not user:
            return {}
        return user.to_dict()

    @jsonize
    @json_body
    @http_status(201)
    def _post(self, request):
        return self.post(request)

    def post(self, request):
        name = request.data.get('name')
        password = request.data.get('password')
        user = User.get(name=name)
        if user and user.validate_password(password):
            user.set_session(request)
            return user.to_dict()
        return {}
