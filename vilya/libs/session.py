# -*- coding: utf-8 -*-
import Cookie
from base64 import b64encode
from datetime import datetime, timedelta
import json
import logging
import os
from time import time

from quixote import get_publisher, session
import redis

from vilya.config import REDIS_URI, SESSION_EXPIRE_DAYS

REDIS = redis.from_url(REDIS_URI)
TTL = SESSION_EXPIRE_DAYS * 24 * 60 * 60
logger = logging.getLogger(__name__)


def randbytes2(bytes):
    return b64encode(os.urandom(bytes)).rstrip('=')


def get_site_cookie(environ, site):
    cookie = Cookie.SimpleCookie()
    if 'HTTP_COOKIE' in environ:
        cookie.load(environ['HTTP_COOKIE'])
        if site in cookie:
            return cookie[site].value


def format_rfc822_date(dt, localtime=True, cookie_format=False):
    if localtime:
        dt = dt - timedelta(hours=8)
    fmt = '%a, %d %b %Y %H:%M:%S GMT'
    if cookie_format:
        fmt = '%a, %d-%b-%Y %H:%M:%S GMT'
    return dt.strftime(fmt)


def format_cookie_date(dt, localtime=True):
    return format_rfc822_date(dt, localtime=True, cookie_format=True)


class SessionManager(session.SessionManager):

    def keys(self):
        return []

    def values(self):
        return []

    def items(self):
        return []

    def get(self, session_id, default=None):
        session = self.session_class.get_session(session_id)
        if session is None:
            session = default
        return session

    def __getitem__(self, session_id):
        return self.get(session_id)

    def has_key(self, session_id):
        return self.get(session_id) is not None

    has_session = has_key

    def __setitem__(self, session_id, session):
        if not isinstance(session, self.session_class):
            raise TypeError("session not an instance of %r: %r"
                            % (self.session_class, session))
        assert session.id is not None, "session ID not set"
        assert session_id == session.id, "session ID mismatch"
        session.save()

    def __delitem__(self, session_id):
        self.session_class.delete_session(session_id)

    def _make_session_id(self):
        session_id = None
        while session_id is None or self.has_session(session_id):
            session_id = session.randbytes(16)
        return session_id

    def get_session(self, request):
        config = get_publisher().config
        session_id = self._get_session_id(request, config)
        session = None
        if session_id is not None:
            session = self.get(session_id)
            if session is not None and (
                config.check_session_addr and
                session.get_remote_address() !=
                request.get_environ("REMOTE_ADDR")
            ):
                logger.debug("Remote IP address does not match the "
                             "IP address that created the session(%s)",
                             session_id)
                session = None

        if session is None:
            session = self._create_session(request)

        session._set_access_time(self.ACCESS_TIME_RESOLUTION)
        return session

    def set_session_cookie(self, request, session_id):
        dt = datetime.now() + timedelta(days=SESSION_EXPIRE_DAYS)
        kwargs = {
            'expires': format_cookie_date(dt, True),
            'httponly': True
        }
        self._set_cookie(request, session_id, **kwargs)


class Session(session.Session):

    def __init__(self, request, id):
        self.redis = REDIS
        self.ttl = TTL
        self.id = id
        self.user = None
        if request is not None:
            self._remote_address = request.get_environ("REMOTE_ADDR")
        self._creation_time = self._access_time = time()
        self._form_tokens = []  # queue

    def _set_access_time(self, resolution):
        session.Session._set_access_time(self, resolution)
        self.save()

    def create_form_token(self):
        token = session.Session.create_form_token(self)
        self.save()
        return token

    def remove_form_token(self, token):
        session.Session.remove_form_token(self, token)
        self.save()

    @staticmethod
    def redis_key(session_id):
        return 'session:' + str(session_id)

    @classmethod
    def get_session(cls, session_id):
        value = REDIS.get(cls.redis_key(session_id))
        if value is not None:
            return cls.loads(value)

    @classmethod
    def delete_session(cls, session_id):
        return REDIS.delete(cls.redis_key(session_id))

    def save(self):
        data = self.dumps()
        self.redis.set(self.redis_key(self.id), data, ex=self.ttl)

    def dumps(self):
        return json.dumps({
            'id': self.id,
            'user': self.user,
            '_form_tokens': self._form_tokens,
            '_remote_address': self._remote_address,
            '_creation_time': self._creation_time,
            '_access_time': getattr(self, '_access_time', None)
        })

    @classmethod
    def loads(cls, data):
        if isinstance(data, basestring):
            dct = json.loads(data)
        else:
            dct = data
        session = cls(None, dct['id'])
        session.redis = REDIS
        session.ttl = TTL
        session.user = dct['user']
        session._form_tokens = dct['_form_tokens']
        session._remote_address = dct['_remote_address']
        session._creation_time = dct['_creation_time']
        if dct['_access_time']:
            session._access_time = dct['_access_time']
        return session
