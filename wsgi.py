#!/usr/bin/python
# coding:utf8

import logging
from logging.handlers import RotatingFileHandler
from werkzeug.debug import DebuggedApplication
from werkzeug.serving import run_simple
from werkzeug.wsgi import DispatcherMiddleware

from app import app

formatter = logging.Formatter(
    "[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")

handler = RotatingFileHandler('vilya.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)

# werkzeug log
#log = logging.getLogger('werkzeug')
#log.setLevel(logging.DEBUG)
#log.addHandler(handler)

app = DebuggedApplication(app, evalex=True)
application = DispatcherMiddleware(app)

if __name__ == "__main__":
    run_simple('0.0.0.0', 8000, application,
               use_reloader=True,
               use_debugger=True,
               processes=1)
