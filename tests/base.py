# encoding: UTF-8

import os
import glob
import unittest
import webtest
import socket

from vilya.libs.rdstore import rds
from vilya.libs.gyt import clear_memoizer
from vilya.libs.store import store

from vilya.models.user import User
from vilya.models.api_key import ApiKey
from vilya.models.gist import Gist
# Notify和Feed这两个引用是必要的的，这样才能使notification和feed的signal正常工作
from vilya.models.notification import Notification  # noqa
from vilya.models.feed import Feed  # noqa

os.environ['CODEDOUBAN_RUNNING_MODE'] = 'unittest'


def _mc_server_flush_all(host, port):
    assert host in ('127.0.0.1', 'localhost', socket.getfqdn())

    sock = socket.socket()
    sock.connect((host, port))
    req = 'flush_all\r\n'
    expected_res = 'OK\r\n'
    assert len(req) == sock.send(req)
    assert sock.recv(1024) == expected_res
    sock.close()


def _flush_mc_server(mc):
    if not hasattr(mc, 'stats'):
        return

    stats = mc.stats()
    assert len(stats) == 1
    host, port = stats.keys()[0].split(':')
    port = int(port)
    _mc_server_flush_all(host, port)


def clear_beansdb_for_test():
    pass


class TestApp(webtest.TestApp):

    """
    The same with `webtest.TestApp`_ except that the app parameter defaults to
    """

    def __init__(self, app=None, **kwargs):
        super(TestApp, self).__init__(app, **kwargs)


def remove_files():
    for p in glob.glob('vilya/permdir/test*'):
        os.removedirs(p)


class TestCase(unittest.TestCase):

    def setUp(self):
        _flush_mc_server(None)
        clear_beansdb_for_test()

    def tearDown(self):
        clear_memoizer()
        rds.flushdb()
        store.rollback_all(force=True)

    def addUser(self, name='unittest_user'):
        return User(name)

    def _add_api_key(self):
        name = 'test'
        desc = ''
        type = ApiKey.TYPE_WEB
        url = 'http://www.douban.com'
        redirect_uri = 'http://www.douban.com/callback'
        owner_id = 'testuser'
        return ApiKey.add(name, desc, type, url, redirect_uri, owner_id)

    def _add_gist(self, description='', owner_id='testuser', is_public=1,
                  gist_names=[], gist_contents=[], fork_from=None):
        return Gist.add(description, owner_id, is_public,
                        gist_names=gist_names, gist_contents=gist_contents,
                        fork_from=fork_from)

    env_for_git = {
        'GIT_AUTHOR_NAME': 'default_test',
        'GIT_AUTHOR_EMAIL': 'default_test@douban.com',
        'GIT_COMMITTER_NAME': 'default_test',
        'GIT_COMMITTER_EMAIL': 'default_test@douban.com',
    }
