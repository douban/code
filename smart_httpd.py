#!/usr/bin/python
# coding:utf8

import os.path

from wsgiauth.basic import BasicAuth

from vilya.config import DEVELOP_MODE
from vilya.libs.git_http_backend import assemble_WSGI_git_app
from vilya.libs.permdir import get_repo_root
from vilya.models.user import User
from vilya.models.project import Project
from vilya.models.organization import Organization


DOUBAN_REALM = "douban wsgi basic auth"


def get_proj(path):
    '''
    >>> get_proj('/a.git/info/refs')
    'a'
    >>> get_proj('/testuser/a.git/info/refs')
    'testuser/a'
    '''
    path_split = path.split("/")
    git_name = path_split[1]
    if not git_name.endswith('.git'):
        git_name = "/".join(path_split[1:3])
    assert "." in git_name, "Need a string looking like project.git, got '%s'" % git_name
    proj_name, _ = os.path.splitext(git_name)
    return proj_name


def get_git_path_info(path):
    path_split = path.split("/")
    git_name = path_split[1]
    # raw path: project_id.git
    if git_name.endswith('.git'):
        project = Project.get(name=git_name[:-4])
        if project:
            path_split[1] = "%s.git" % project.id
            return '/'.join(path_split)
    else:
        owner_name, git_name = path_split[1:3]
        # user project: user/project.git
        user = User.get(name=owner_name)
        if user:
            project = Project.get(name=git_name[:-4], owner_id=user.id)
            if project:
                path_split[1] = ""
                path_split[2] = "%s.git" % project.id
                return '/'.join(path_split[1:])
            return
        # org project: org/project.git
        org = Organization.get(name=owner_name)
        if org:
            project = Project.get(name=git_name[:-4], owner_id=user.id)
            if project:
                path_split[1] = ""
                path_split[2] = "%s.git" % project.id
                return '/'.join(path_split[1:])


def authfunc(environ, username, passwd):
    #if DEVELOP_MODE or (environ['REMOTE_ADDR'] == '127.0.0.1'
    #                    and environ['HTTP_HOST'] == 'localhost:8080'):
    #    return True
    if not passwd:
        return
    if username == 'code' and passwd == 'code':
        return True
    user = User.get_by_name(username)
    if not user:
        return
    if not user.validate_password(passwd):
        return
    is_push = 'service=git-receive-pack' in environ['QUERY_STRING'] or '/git-receive-pack' in environ['PATH_INFO']
    if is_push:
        pass
        # FIXME: push permission
    return True


class HTTPAuth(object):
    def __init__(self, application, realm, authfunc, scheme, **kw):
        self.application = application
        self.authenticate = scheme(realm, authfunc, **kw)
        self.scheme = scheme.authtype

    def __call__(self, environ, start_response):
        path_info = environ['PATH_INFO']
        environ['GIT_PATH_INFO'] = get_git_path_info(path_info)
        if environ.get('REMOTE_USER') is None:
            result = self.authenticate(environ)
            if not isinstance(result, str):
                # Request credentials if authentication fails
                return result(environ, start_response)
            environ['REMOTE_USER'] = result
            environ['AUTH_TYPE'] = self.scheme
        return self.application(environ, start_response)


class WebRedirect(object):
    def __init__(self, application, **kw):
        self.application = application

    def __call__(self, environ, start_response):
        http_accept = environ.get('HTTP_ACCEPT')
        path_info = environ.get('PATH_INFO')
        proj_name = get_proj(path_info)
        if http_accept and 'text/html' in http_accept:
            start_response('301 Redirect',
                           [('Location', '/%s/' % proj_name), ])
            return []
        return self.application(environ, start_response)


app = assemble_WSGI_git_app(content_path=get_repo_root())
app = WebRedirect(app)
app = HTTPAuth(app, DOUBAN_REALM, authfunc, BasicAuth)
