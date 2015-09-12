# -*- coding: utf-8 -*-
import uuid
from quixote.errors import PublishError
from vilya.libs.store import mc

OAUTH_USER_CODE = 'oauth:%s:%s:code'
OAUTH_CONFIRM = 'oauth:%s:%s:confirm'

ONE_MINUTE = 60
TEN_MINUTES = ONE_MINUTE * 10


class OAuthCode(object):

    def __init__(self, apikey, user_id):
        self.code = uuid.uuid1().hex[:20]
        mc.set(self.__mc_key(apikey, self.code), user_id, TEN_MINUTES)

    @classmethod
    def __mc_key(cls, apikey, code):
        return OAUTH_USER_CODE % (apikey, code)

    @classmethod
    def check(cls, apikey, code):
        key = cls.__mc_key(apikey, code)
        user_id = mc.get(key)
        if user_id:
            mc.delete(key)
        return user_id


class OAuthConfirm(object):

    def __init__(self, user_id):
        self.cid = uuid.uuid1().hex[:20]
        mc.set(OAUTH_CONFIRM % (user_id, self.cid), 1, ONE_MINUTE)

    @classmethod
    def confirm(cls, user_id, cid):
        key = OAUTH_CONFIRM % (user_id, cid)
        if mc.get(key):
            mc.delete(key)
            return True


class OAuthError(PublishError):

    def __init__(self, code, msg):
        self.private_msg = None
        self.public_msg = None
        self.status_code = code
        self.message = msg

    def __str__(self):
        return "status: %s, reason: %s" % (self.status_code, self.message)
