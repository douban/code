#!/usr/bin/python
# coding:utf8

import os
import sys
import time
import traceback
from quixote.qwip import QWIP
from quixote.publish import SessionPublisher

from werkzeug.debug import DebuggedApplication

from vilya import views as controllers
from vilya.config import DEVELOP_MODE
from vilya.libs.gzipper import make_gzip_middleware
from vilya.libs.permdir import get_tmpdir
from vilya.libs.import_obj import import_obj_set
from vilya.libs.template import st
from vilya.libs.auth.check_auth import check_auth
from vilya.models.user import User
from vilya.views.util import is_mobile_device


class CODEPublisher(SessionPublisher):

    def __init__(self, *args, **kwargs):
        SessionPublisher.__init__(self, *args, **kwargs)
        self.configure(DISPLAY_EXCEPTIONS='plain',
                       SECURE_ERRORS=0,
                       DEBUG_PROPAGATE_EXCEPTIONS=DEVELOP_MODE,
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
        request.user = None
        check_auth(request)  # OAuth
        if request.user is None:
            request.user = User.get_current_user()

        import_obj_set("request", request)

    def try_publish(self, request, path):
        output = SessionPublisher.try_publish(self, request, path)
        return output

    def finish_failed_request(self, request):
        if DEVELOP_MODE:
            exc_type, exc_value, tb = sys.exc_info()
            raise exc_type, exc_value, tb
        else:
            return SessionPublisher.finish_failed_request(self, request)

    def _generate_cgitb_error(self, request, original_response,
                              exc_type, exc_value, tb):
        traceback.print_exc()
        return st('/errors/500.html', **locals())


def create_publisher():
    return CODEPublisher(controllers)

app = make_gzip_middleware(QWIP(create_publisher()))
if DEVELOP_MODE:
    app = DebuggedApplication(app, evalex=True)
