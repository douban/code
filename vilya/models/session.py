# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from vilya.libs.session import (randbytes2,
                                get_site_cookie,
                                format_cookie_date)
from vilya.config import (SESSION_EXPIRE_DAYS,
                          SESSION_DOMAIN,
                          SESSION_COOKIE_NAME)


class SessionMixin(object):

    @classmethod
    def check_session(cls, request):
        cookie = get_site_cookie(request.environ, SESSION_COOKIE_NAME)
        if not cookie:
            return

        uid = key = ''
        x = cookie.split(':')
        if len(x) == 2:
            uid, key = x
        if not uid:
            return
        user = cls.get(id=uid)
        if user and user.is_valid_session(key):
            return user

    def set_session(self, request, remember=True, domain=SESSION_DOMAIN):
        if not self.has_valid_session():
            self.create_session()

        dict = {'domain': domain, 'httponly': 'True'}
        if remember:
            dt = datetime.now() + timedelta(days=SESSION_EXPIRE_DAYS)
            dict['expires'] = format_cookie_date(dt, True)

        request.response.set_cookie(SESSION_COOKIE_NAME,
                                    '%s:%s' % (self.id, self.session_id),
                                    path='/',
                                    **dict)

    def has_valid_session(self):
        if not self.session_id:
            return False

        if self.session_expired_at \
                and self.session_expired_at >= datetime.now():
            return True

    def is_valid_session(self, session):
        if not self.has_valid_session():
            return False
        return session == self.session_id

    def clear_session(self):
        self.session_id = None
        self.save()

    def create_session(self):
        session_id = randbytes2(8)
        expired_time = datetime.now() + timedelta(days=SESSION_EXPIRE_DAYS)
        self.session_expired_at = expired_time
        self.session_id = session_id
        self.save()
