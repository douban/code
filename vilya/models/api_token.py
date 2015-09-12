# -*- coding: utf-8 -*-
import uuid
from datetime import datetime, timedelta

from vilya.libs.store import store
from vilya.models.api_key import ApiKey
from vilya.models.user import User

NORMAL = 0


class ApiToken(object):

    def __init__(self, id, client_id, user_id, token, expire_time,
                 refresh_token, refresh_expire_time, status, created_at):
        self.id = id
        self.client_id = client_id
        self.user_id = user_id
        self.token = token
        self.expire_time = expire_time
        self.refresh_token = refresh_token
        self.refresh_expire_time = refresh_expire_time
        self.status = status
        self.created_at = created_at

    def __eq__(self, target):
        return self.id == target.id and self.client_id == target.client_id \
            and self.token == target.token

    @classmethod
    def get(cls, id):
        rs = store.execute("select `id`,`client_id`,`user_id`,`token`,`expire_time`, "
                           "`refresh_token`,`refresh_expire_time`,`status`,`created_at` "
                           "from api_token where id=%s", (id,))
        return rs and cls(*rs[0]) or None

    @classmethod
    def get_by_token(cls, token):
        rs = store.execute("select `id`,`client_id`,`user_id`,`token`,`expire_time`, "
                           "`refresh_token`,`refresh_expire_time`,`status`,`created_at` "
                           "from api_token where token=%s", (token,))
        return rs and cls(*rs[0]) or None

    @classmethod
    def get_by_refresh_token(cls, refresh_token):
        rs = store.execute("select `id`,`client_id`,`user_id`,`token`,`expire_time`, "
                           "`refresh_token`,`refresh_expire_time`,`status`,`created_at` "
                           "from api_token where refresh_token=%s", (refresh_token,))
        return rs and cls(*rs[0]) or None

    def refresh(self):
        self.revoke()
        return self.add(self.client_id, self.user_id)

    def revoke(self):
        now = datetime.now()
        store.execute("update api_token set expire_time=%s, refresh_expire_time=%s "
                      "where id=%s", (now, now, self.id))
        store.commit()
        self.expire_time = self.refresh_expire_time = now

    @classmethod
    def add(cls, client_id, user_id, expire_time=None, status=NORMAL):
        if not ApiKey.get_by_client_id(client_id):
            return

        now = datetime.now()
        if not expire_time:
            expire_time = now + timedelta(days=7)
        refresh_expire_time = expire_time + timedelta(days=7)

        token = uuid.uuid4().hex
        refresh_token = uuid.uuid4().hex
        id = store.execute("insert into api_token (`client_id`,`user_id`,`token`,`expire_time`, "
                           "`refresh_token`, `refresh_expire_time`, `status`, `created_at`) "
                           "values(%s, %s, %s, %s, %s, %s, %s, %s)",
                           (client_id, user_id, token, expire_time, refresh_token, refresh_expire_time, status, now))
        store.commit()
        return id and cls.get(id)

    def token_dict(self):
        remain = self.expire_time - datetime.now()
        return dict(user_id=self.user_id, access_token=self.token,
                    refresh_token=self.refresh_token, expires_in=remain.seconds)

    @property
    def user(self):
        return User(self.user_id)

    @property
    def key(self):
        return ApiKey.get_by_client_id(self.client_id)
