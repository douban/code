#!/usr/bin/env python
# encoding: utf-8

import json
import httplib
import socket
import ssl

from vilya.libs.store import bdb
from vilya.libs.mq import async

IOS_APP_ID_NAME = 'app_id'
IOS_REST_API_KEY_NAME = 'rest_api_key'
IOS_MASTER_KEY_NAME = 'master_key'

API_BASE = "api.parse.com"
GET_INSTALLATIONS_PATH = "/1/installations"
GET_INSTALLATION_PATH = "/1/installations/%s"
PUSH_PATH = "/1/push"

BDB_API_KEY = 'code_push_notification_key:1'

_RETRY = 3
_TIMEOUT = 20
_api_keys = {}


def set_api_keys(app_id, rest_api_key, master_key):
    _api_keys[IOS_APP_ID_NAME] = app_id
    _api_keys[IOS_REST_API_KEY_NAME] = rest_api_key
    _api_keys[IOS_MASTER_KEY_NAME] = master_key
    keys = json.dumps(_api_keys)
    bdb.set(BDB_API_KEY, keys)


def get_api_keys():
    keys = bdb.get(BDB_API_KEY)
    keys = json.loads(keys) if keys else {}
    for k in keys:
        _api_keys[k] = keys[k]


def validate_api_keys():
    if not _api_keys:
        get_api_keys()
    for k in (IOS_APP_ID_NAME, IOS_REST_API_KEY_NAME, IOS_MASTER_KEY_NAME):
        v = _api_keys.get(k)
        if not (v and isinstance(v, basestring)):
            return False
    return True


def set_api_key(key, value):
    _api_keys[key] = value


def get_api_key(key):
    return _api_keys[key]


def request(method, path, data):
    connection = httplib.HTTPSConnection(API_BASE, 443, timeout=_TIMEOUT)
    connection.connect()
    connection.request(
        method,
        path,
        json.dumps(data),
        {
            'X-Parse-Application-Id': _api_keys[IOS_APP_ID_NAME],
            'X-Parse-Master-Key': _api_keys[IOS_MASTER_KEY_NAME],
            'X-Parse-REST-API-Key': _api_keys[IOS_REST_API_KEY_NAME],
            'Content-Type': 'application/json'
        }
    )
    return json.loads(connection.getresponse().read())


def get_channels():
    installations = request('GET', GET_INSTALLATIONS_PATH, {})
    results = installations.get('results')
    if results:
        return reduce(
            (lambda x, y: x+y),
            [r.get('channels') for r in results])


def _send(data):
    if not validate_api_keys():
        return
    channels = get_channels()
    if channels:
        result = request(
            'POST',
            PUSH_PATH,
            {'channels': channels, 'data': data}
        )
        return result


def send(data):
    for i in range(_RETRY):
        try:
            rs = _send(data)
            if rs:
                return rs
        except socket.timeout:
            continue
        except ssl.SSLError:
            continue


@async()
def send_alert(alert):
    return send({'alert': alert})


if __name__ == '__main__':
    print send_alert(
        '再测试一下正常的发送消息,测试成功貌似就没问题了'
        '记录发送失败的功能回来再做吧'
    )
