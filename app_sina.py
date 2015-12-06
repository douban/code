# coding:utf8
import os
import select
import subprocess
from wsgiauth.basic import BasicAuth

from gevent.monkey import get_original
try:
    select.poll = get_original('select', 'poll')
except AttributeError:
    select.poll = get_original('select', 'kqueue')
subprocess.Popen = get_original('subprocess', 'Popen')

from sina import Sina
from sina.config import DEFAULT_CONFIG

from vilya.config import DEVELOP_MODE
from vilya.libs.permdir import get_repo_root
from vilya.models.project import CodeDoubanProject
from vilya.models.gist import Gist
from vilya.models.user import User

DOUBAN_REALM = "douban wsgi basic auth"
DEFAULT_CONFIG['project_root'] = get_repo_root()
app = Sina(DEFAULT_CONFIG)


# @app.get_repo_path
def get_repo_path_handler(environ, path):
    return ''


# @app.before_request
def before_request_handler(environ):
    return


@app.has_permission
def has_permission_handler(environ, path, perm):

    if DEVELOP_MODE:
        return True

    username = environ.get('REMOTE_USER')

    # if len(path) < 4:
    #    return
    name = path[:-4]

    # gist
    if name.startswith('gist/'):
        gist_id = name.rpartition("/")[-1]
        gist = Gist.get(gist_id)
        if not gist:
            return

        if perm == 'read':
            return True

        if not username:
            return

        return gist.owner_id == username

    # project
    project = CodeDoubanProject.get_by_name(name)
    if not project:
        return

    if perm == 'read':
        return True

    if not username:
        return
    if not project.can_push:
        # merge only
        return
    return project.has_push_perm(username)


def authfunc(env, username, passwd):
    if DEVELOP_MODE or (env['REMOTE_ADDR'] == '127.0.0.1'
                        and env['HTTP_HOST'] == 'localhost:8080'):
        return True

    if not passwd:
        return

    if username == 'code' and passwd == 'code':
        return True

    user = User.get_by_name(username)
    if user and user.validate_password(passwd):
        return True

    is_push = 'service=git-receive-pack' in env['QUERY_STRING'] \
              or '/git-receive-pack' in env['PATH_INFO']
    if is_push:
        pass
        # FIXME: push permission
    return True


def is_git_push_url(url, query=None):
    if 'service=git-receive-pack' in query:
        return True
    if '/git-receive-pack' in url:
        return True
    return False


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
    assert "." in git_name, "Need a string looking like project.git, got '%s'" % git_name  # noqa
    proj_name, _ = os.path.splitext(git_name)
    return proj_name


class HTTPAuth(object):
    def __init__(self, application, realm, authfunc, scheme, **kw):
        self.application = application
        self.authenticate = scheme(realm, authfunc, **kw)
        self.scheme = scheme.authtype

    def __call__(self, environ, start_response):
        if not is_git_push_url(environ['PATH_INFO'], environ['QUERY_STRING']):
            # passthrough basic auth
            return self.application(environ, start_response)

        if environ.get('REMOTE_USER') is None:
            result = self.authenticate(environ)
            if not isinstance(result, str):
                # Request credentials if authentication fails
                return result(environ, start_response)
            environ['REMOTE_USER'] = result
            # git hook env
            environ['env'] = {'CODE_REMOTE_USER': result}
            environ['AUTH_TYPE'] = self.scheme
        return self.application(environ, start_response)


class GitDispatcher(object):

    def __init__(self, git_app, web_app):
        self.instances = {
            'git_app': git_app,
            'web_app': web_app,
        }

    def get_application(self, user_agent):
        if user_agent and 'git' not in user_agent:
            return self.instances['web_app']
        return self.instances['git_app']

    def __call__(self, environ, start_response):
        user_agent = environ.get('HTTP_USER_AGENT')
        app = self.get_application(user_agent)
        return app(environ, start_response)


class RedirectWeb(object):

    def __call__(self, environ, start_response):
        path_info = environ.get('PATH_INFO')
        proj_name = get_proj(path_info)
        start_response('301 Redirect', [('Location', '/%s/' % proj_name), ])
        return []


redirect_app = RedirectWeb()
app = HTTPAuth(app, DOUBAN_REALM, authfunc, BasicAuth)
app = GitDispatcher(git_app=app, web_app=redirect_app)
