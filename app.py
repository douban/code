# -*- coding: utf-8 -*-

import re
from gevent import monkey; monkey.patch_all()
from web import app as web
from app_sina import app as git_http
from vilya.wsgi import application as django_app


ROUTE_MAP = [(re.compile(r'/[^/]*\.git.*'), git_http),
             (re.compile(r'/[^/]*/([^/]*)\.git.*'), git_http),
             (re.compile(r'/admin'), django_app),
             (re.compile(r'/people'), django_app),
             (re.compile(r'/gist'), django_app),
             (re.compile(r'/register'), django_app),
             (re.compile(r'/login'), django_app),
             (re.compile(r'/logout'), django_app),
             (re.compile(r'/mirrors'), django_app),
             (re.compile(r'/badge'), django_app),
             (re.compile(r'/vilya'), django_app),
             (re.compile(r'/.*'), web)]


class Application(object):

    def __call__(self, environ, start_response):
        for rule, func in ROUTE_MAP:
            if rule.match(environ['PATH_INFO']):
                return func(environ, start_response)
        return web(environ, start_response)

app = Application()
