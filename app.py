# -*- coding: utf-8 -*-

from argparse import ArgumentParser
import re

from werkzeug.serving import run_simple
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

    def run(self, host='127.0.0.1', port=8200, debug=False, **options):
        options.setdefault('use_reloader', debug)
        options.setdefault('use_debugger', debug)
        run_simple(host, port, self, **options)

app = Application()

if __name__ == '__main__':
    parser = ArgumentParser(description='run the development server')
    parser.add_argument('--host', default='127.0.0.1',
                        help='host(default: 127.0.0.1)')
    parser.add_argument('--port', default=8200, type=int,
                        help='port(default: 8200)')
    parser.add_argument('-D', '--no-debug', action='store_true',
                        help='disable the Werkzeug debugger')
    parser.add_argument('-R', '--no-reload', action='store_true',
                        help='do not monitor Python files for changes')
    args = parser.parse_args()

    host = args.host
    port = args.port
    use_debugger = not args.no_debug
    use_reloader = not args.no_reload
    app.run(host=host, port=port, use_debugger=use_debugger,
            use_reloader=use_reloader)
