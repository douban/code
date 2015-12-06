# -*- coding: utf-8 -*-
import uuid
from datetime import datetime

from vilya.libs.store import store


class ApiKey(object):

    TYPE_WEB = 0
    TYPE_DESKTOP = 1
    TYPE_MOBILE = 2

    STATUS_DEV = 0
    STATUS_NORMAL = 1
    STATUS_BLOCKED = 2

    def __init__(self, id, name, description, type,
                 url, redirect_uri, owner_id, client_id, client_secret,
                 status, created_at, updated_at):

        self.id = id
        self.name = name.decode('utf-8')
        self.description = description.decode('utf-8')
        self.type = type
        self.url = url
        self.redirect_uri = redirect_uri
        self.owner_id = owner_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at

    def __eq__(self, target):
        return self.id == target.id and self.client_id == target.client_id

    @classmethod
    def get(cls, id):
        rs = store.execute("select `id`,`name`,`description`,`type`,`url`,`redirect_uri`,"
                           "`owner_id`,`client_id`,`client_secret`,`status`, `created_at`,`updated_at` "
                           "from api_key where id=%s", (id,))
        return rs and cls(*rs[0]) or None

    @classmethod
    def get_by_client_id(cls, client_id):
        rs = store.execute("select `id`,`name`,`description`,`type`,`url`,`redirect_uri`,"
                           "`owner_id`,`client_id`,`client_secret`,`status`, `created_at`,`updated_at` "
                           "from api_key where client_id=%s", (client_id,))
        return rs and cls(*rs[0]) or None

    @classmethod
    def add(cls, name, description, type, url, redirect_uri, owner_id):
        now = datetime.now()
        client_id = uuid.uuid1().hex[:20]
        client_secret = uuid.uuid4().hex
        id = store.execute("insert into api_key "
                           "(`name`,`description`,`type`,`url`,`redirect_uri`,`owner_id`,"
                           "`client_id`,`client_secret`,`created_at`,`updated_at`) "
                           "values(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                           (name, description, type, url, redirect_uri, owner_id,
                            client_id, client_secret, now, now))
        store.commit()
        return id and cls.get(id)
