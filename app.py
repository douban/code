# -*- coding: utf-8 -*-

import re

from web import app as web
from app_sina import app as git_http


ROUTE_MAP = [(re.compile(r'/[^/]*\.git.*'), git_http),
             (re.compile(r'/[^/]*/([^/]*)\.git.*'), git_http),
             (re.compile(r'/.*'), web)]


class Application(object):

    def __call__(self, environ, start_response):
        for rule, func in ROUTE_MAP:
            if rule.match(environ['PATH_INFO']):
                return func(environ, start_response)
        return web(environ, start_response)

app = Application()
