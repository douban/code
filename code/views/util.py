# -*- coding: utf-8 -*-

from __future__ import absolute_import

import re
import json
from functools import wraps
from quixote.errors import TraversalError

from code.libs.template import st, request
from code.libs.diff import LineHtml

RE_MOBILE = re.compile(r"""
                       android.+mobile|samsumg|avantgo|bada\\/|blackberry|
                       blazer|compal|elaine|fennec|iphone|ipod|iris|kindle|
                       maemo|meego.+mobile|mmp|netfront|opera m(ob|in)i|
                       palm( os)?|phone|p(ixi|re)\\/|plucker|pocket|psp|
                       series40|series60|symbian|treo|up\\.(browser|link)|
                       j2me|midp|cldc|vodafone|wap|windows (ce|phone)
                       """, re.I | re.M)
RE_OS_IN_USER_AGENT = re.compile("(windows|mac(?= os x)|iphone|android|linux)(?= )")
RE_BROWSER_IN_USER_AGENT = re.compile("((?<= )msie \d{1,2}|(?<=)firefox\/\d{1,2}|webkit(?=[ \/]))|\\bopera\\b")


def jsonize(func):
    @wraps(func)
    def _(*a, **kw):
        return json.dumps(func(*a, **kw))
    return _


def json_body(func):
    def _(*args, **kwargs):
        body = request.stdin.read()
        if body:
            try:
                request.data = json.loads(body)
            except ValueError:
                return error_message("invalid body")
        return func(*args, **kwargs)
    return _


def error_message(msg):
    return json.dumps({"error": msg})


def require_login_json(func):
    def _(*args, **kwargs):
        user = request.user
        if not user:
            return error_message("not login")
        return func(*args, **kwargs)
    return _


def require_login(func):
    def _(*args, **kwargs):
        user = request.user
        if not user:
            return request.redirect("/hub/projects")
        return func(*args, **kwargs)
    return _


def http_method(methods=None):
    def decorator(f):
        def decorated(*args, **kwargs):
            if methods is not None:
                if request.method in methods:
                    return f(*args, **kwargs)
                else:
                    raise TraversalError()

            return f(*args, **kwargs)
        return decorated
    return decorator


def client_class(request):
    agent = request.environ.get('HTTP_USER_AGENT')
    if not agent:
        return ''
    agent = agent.lower()

    os_res = RE_OS_IN_USER_AGENT.search(agent)
    os_str = "ua-%s " % os_res.group() if os_res else ""

    br_res = RE_BROWSER_IN_USER_AGENT.search(agent)
    br_str = br_res.group() if br_res else ""

    if br_str.startswith('m'):
        br_str = "ua-ie" + br_str[5:]
    elif br_str.startswith('f'):
        br_str = "ua-ff" + br_str[8:]
    elif br_str == 'opera':
        br_str = 'ua-opera'
    elif br_str:
        br_str = "ua-" + br_str

    return os_str + br_str


def is_mobile_device(request):
    user_agent = request.get_header('user-agent')
    if user_agent:
        return RE_MOBILE.search(user_agent)
    return False


def render_action(action, is_notify, show_avatar):
    return st('widgets/feed_action.html', **locals())


def render_actions(actions, show_avatar, is_render_actions=True, is_collapsed=True):
    return st('widgets/actions_feed.html', **locals())


def render_message(message):
    return st('widgets/chat_message.html', **locals())

linehtml = LineHtml()
