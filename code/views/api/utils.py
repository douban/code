# -*- coding: utf-8 -*-

import json
from functools import wraps
import datetime

from code.models.user import User
from code.libs.template import request as req
from code.views.api import errors

from quixote.publish import get_publisher


API_RESULT_DEFAULT_PER_PAGE = 20


class DatetimeEncoder(json.JSONEncoder):
    """
    Provide encoder for datetime object
    """

    def default(self, obj):
        if isinstance(obj, datetime.datetime) or isinstance(obj,datetime.date):
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
                raise errors.NotJsonError
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
            raise errors.UnauthorizedError
        return fn(*args, **kwargs)
    return wrapper


def api_list_user(users):
    rs = []
    for username in users:
        user = User.get_by_name(username)
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
            raise errors.MethodNotAllowedError

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
        raise NotImplementedError("You need to implement this method in subclass")

    def post(self, req):
        raise NotImplementedError("You need to implement this method in subclass")

    def put(self, req):
        raise NotImplementedError("You need to implement this method in subclass")

    def patch(self, req):
        raise NotImplementedError("You need to implement this method in subclass")

    def delete(self, req):
        raise NotImplementedError("You need to implement this method in subclass")

class APIRootBase(object):
    _q_exports = []

    def __call__(self, request):
        return self._q_index(request)

    @jsonize
    def _q_index(self, request):
        """
        index view of api root, just return a dictionary with current api version
        :returns: a json string gives the current api version
        """
        return {"api_version": self.version_string}

    @property
    def version(self):
        """
        tuple of current api version, the first item of tuple is the main version of api,
        the second item of the tuple represents sub version, the subversion should be updated
        everytime you revise current version.

        :returns: a tuple contains 2 elements that present, eg:(1, 0)
        """
        raise NotImplementedError

    @property
    def version_string(self):
        """
        join version tuple into string
        :returns: string presents current version, eg. 1.0
        """
        return '.'.join(map(str,self.version))

    def _publish(self, part):
        if part in self._q_exports:
            obj = getattr(self, part) 
            if obj:
                return obj
            elif hasattr(self, '_q_resolve'):
                return self._q_resolve(part)
        raise errors.NotFoundError()
    
    def publish(self, request, part):
        """
        this function works as a simple publisher class for request sent to default version
        
        :part: the first component of the request
        :returns: a quixote compatible ui object or module
        """
        publisher = get_publisher()
        publisher.namespace_stack.append(self)
        return self._publish(part)

    def _q_exception_handler(self, request, exception):
        """
        quixote exception handler, dumps error object into json representation
        :returns: a json string gives the error infomation
                  eg: {'code':404,
                        'type':'Not Found',
                        'api_version':'1.0',
                        'message':'some message',}
        """
        from quixote import errors as quixote_errors 

        if isinstance(exception, errors.CodeAPIError):
            pass
        elif isinstance(exception, quixote_errors.TraversalError):
            exception = errors.NotFoundError()
        elif isinstance(exception, quixote_errors.AccessError):
            exception = errors.ForbiddenError()
        else:
            # raise the exception here to debug, cause a non-PublishError is raised
            raise exception

        error_data = exception.to_dict()
        error_data['api_version'] = self.version_string
        request.response.set_content_type('application/json; charset=utf-8')
        return json.dumps(error_data)


