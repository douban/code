# -*- coding: utf-8 -*-

import json
import datetime
from functools import wraps

from vilya.models.user import User
from vilya.libs import api_errors
from vilya.libs.template import request as req

API_RESULT_DEFAULT_PER_PAGE = 20


class DatetimeEncoder(json.JSONEncoder):
    """
    Provide encoder for datetime object
    """

    def default(self, obj):
        if isinstance(obj, datetime.datetime) or isinstance(
                obj, datetime.date):
            return obj.isoformat()
        else:
            return json.JSONEncoder.default(self, obj)

def jsonize(func):
    @wraps(func)
    def _(*a, **kw):
        body = func(*a, **kw)
        # if the body is empty return "", so the response body is empty
        # NOTE: empety array in a resaonble response
        if body or body == []:
            return json.dumps(body, cls=DatetimeEncoder)
        else:
            return ""
    return _


def json_body(func):
    def _(*args, **kwargs):
        body = req.stdin.read()
        if body:
            try:
                req.data = json.loads(body)
            except ValueError:
                raise api_errors.NotJSONError
        else:
            req.data = {}
        return func(*args, **kwargs)
    return _


def http_status(status_code):
    def status_decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            req.response.set_status(int(status_code))
            return fn(*args, **kwargs)
        return wrapper
    return status_decorator


def pagination(func):
    def _(*args, **kwargs):
        try:
            req.page = int(req.get_form_var('page'))
        except TypeError:
            req.page = 0
        try:
            req.count = int(req.get_form_var('count'))
        except TypeError:
            req.count = API_RESULT_DEFAULT_PER_PAGE
        return func(*args, **kwargs)
    return _


def api_require_login(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not req.user:
            raise api_errors.UnauthorizedError
        return fn(*args, **kwargs)
    return wrapper


def api_list_user(users):
    rs = []
    for username in users:
        user = User(username)
        rs.append({'username': user.username,
                   'avatar_url': user.avatar_url,
                   'email': user.email,
                   'url': user.url, })
    return rs


class RestAPIUI(object):
    _q_exports = []
    _q_methods = []

    def _q_index(self, req):
        method = req.method.lower()
        if method not in self._q_methods:
            raise api_errors.MethodNotAllowedError

        self.user = req.user
        endpoints = {
            "get": self._get,
            "post": self._post,
            "put": self._put,
            "patch": self._patch,
            "delete": self._delete
        }

        return endpoints[method](req)

    @jsonize
    def _get(self, req):
        return self.get(req)

    @jsonize
    @json_body
    @http_status(201)
    @api_require_login
    def _post(self, req):
        return self.post(req)

    @jsonize
    @json_body
    @api_require_login
    def _put(self, req):
        return self.put(req)

    @jsonize
    @json_body
    @api_require_login
    def _patch(self, req):
        return self.patch(req)

    @http_status(204)
    @api_require_login
    def _delete(self, req):
        self.delete(req)
        return ""

    def get(self, req):
        raise NotImplementedError(
            "You need to implement this method in subclass")

    def post(self, req):
        raise NotImplementedError(
            "You need to implement this method in subclass")

    def put(self, req):
        raise NotImplementedError(
            "You need to implement this method in subclass")

    def patch(self, req):
        raise NotImplementedError(
            "You need to implement this method in subclass")

    def delete(self, req):
        raise NotImplementedError(
            "You need to implement this method in subclass")
