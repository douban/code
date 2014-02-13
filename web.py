#!/usr/bin/python
# coding:utf8

import os
import time
import traceback

from quixote.publish import SessionPublisher
from quixote.qwip import QWIP
from quixote.session import SessionManager

from code.libs.gzipper import make_gzip_middleware
from code.libs.permdir import get_tmpdir
from code.libs.auth.check_auth import check_auth
from code.libs.import_obj import import_obj_set
from code.libs.template import st
from code.views.util import is_mobile_device

import code.views as controllers


PERFORMANCE_METRIC_MARKER = '<!-- _performtips_ -->'


def show_performance_metric(request, output):
    idx = output.find(PERFORMANCE_METRIC_MARKER)
    if idx > 0:
        pt = int((time.time() - request.start_time) * 1000)
        cls = pt > 250 and 'red' or pt > 100 and 'orange' or 'green'
        block = '<li class="hidden-phone"><a href="?_dae_profile=1" style="color:%s"> %d ms </a></li>' % (cls, pt)
        output = (output[:idx] + block + output[idx + len(PERFORMANCE_METRIC_MARKER):])
    return output


class CodePublisher(SessionPublisher):

    def __init__(self, *args, **kwargs):
        SessionPublisher.__init__(self, *args, **kwargs)
        display = 'html' if os.environ.get('DOUBAN_PRODUCTION') else 'plain'
        self.configure(DISPLAY_EXCEPTIONS=display,
                       UPLOAD_DIR=get_tmpdir() + '/upload/')

    def start_request(self, request):
        SessionPublisher.start_request(self, request)
        os.environ['SQLSTORE_SOURCE'] = request.get_url()

        resp = request.response
        resp.set_content_type('text/html; charset=utf-8')
        resp.set_header('Pragma', 'no-cache')
        resp.set_header('Cache-Control', 'must-revalidate, no-cache, private')
        # FIXME: quixote with origin?
        resp.set_header('Access-Control-Allow-Origin', '*')
        request.enable_ajax = False
        request.browser = request.guess_browser_version()
        request.method = request.get_method()
        request.url = request.get_path()
        request.is_mobile = is_mobile_device(request)
        request.start_time = time.time()
        # FIXME: user login
        request.user = None
        check_auth(request)  # OAuth

        import_obj_set("request", request)

    def try_publish(self, request, path):
        output = SessionPublisher.try_publish(self, request, path)
        output = show_performance_metric(request, output)
        return output

    def _generate_cgitb_error(self, request, original_response, exc_type, exc_value, tb):
        if os.environ.get('DAE_ENV') == 'SDK':
            traceback.print_exc()
            return st('/errors/500.html', **locals())

        traceback.print_exc()
        return st('/errors/500.html', **locals())


def create_publisher():
    return CodePublisher(controllers,
                         session_mgr=SessionManager())


app = make_gzip_middleware(QWIP(create_publisher()))
