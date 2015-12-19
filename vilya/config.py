# coding: utf-8

import ast
import os
from os.path import dirname, abspath

from libmc import MC_HASH_MD5

DEVELOP_MODE = False


DAE_ENV = os.environ.get('DAE_ENV')
CSS_JS_DEVELOP_MODE = DAE_ENV == 'SDK'


CODE_DIR = dirname(abspath(__file__))
HOOKS_DIR = os.path.join(CODE_DIR, 'hooks')
REPO_DIR = os.path.join(CODE_DIR, 'permdir')

# session
SESSION_EXPIRE_DAYS = 14
SESSION_DOMAIN = ''
SESSION_COOKIE_NAME = 'code_user'


MEMCACHED_HOSTS = os.environ.get('DOUBAN_CODE_MEMCACHED_HOSTS',
                                 '127.0.0.1:11311').split(',')
MEMCACHED_CONFIG = {
    'do_split': True,
    'comp_threshold': 0,
    'noreply': False,
    'prefix': None,
    'hash_fn': MC_HASH_MD5,
    'failover': False
}

DOUBANDB = {
    'servers': os.environ.get('DOUBAN_CODE_DOUBANDB_SERVERS',
                              '127.0.0.1:11311').split(','),
    'proxies': os.environ.get('DOUBAN_CODE_DOUBANDB_PROXIES',
                              '').split(',')
}

_default_mysql_store = {
    "farms": {
        "code_farm": {
            "master": "localhost:3306:valentine:root:",
            "tables": ["*"],
        }
    }
}
MYSQL_STORE = ast.literal_eval(
    os.environ.get('DOUBAN_CODE_MYSQL_STORE', '{}')
) or _default_mysql_store


REDIS_URI = os.environ.get('DOUBAN_CODE_REDIS_URI', 'redis://localhost:6379/0')

_beansdb_hosts = os.environ.get(
    'DOUBAN_CODE_BEANSDB_HOSTS',
    'localhost:7901,localhost:7902,localhost:7903'
).split(',')
BEANSDBCFG = {host: range(16) for host in _beansdb_hosts}

DOMAIN = os.environ.get('DOUBAN_CODE_DOMAIN', 'http://127.0.0.1:8200')
IRC_SERVER = 'irc.intra.douban.com'
IRC_PORT = 12345
SMTP_SERVER = 'mail.douban.com'

MAKO_FS_CHECK = True

EMAIL_SUFFIX = 'douban.com'
DEFAULT_SENDER_ADDR = 'code@douban.com'
DEFAULT_NOTIFY_SENDER_ADDR = 'code-notification@douban.com'
CUSTOMIZE_NOTIFY_SENDER_ADDR = 'code-notification+%s+code@douban.com'
TRASH_EMAIL_ADDR = 'code-email-trash@dappsmail.douban.com'

TRELLO_CONSUMER_KEY = ''
TRELLO_CONSUMER_SECRET = ''

# bcrypt_sha256/bcrypt
PASSWORD_METHOD = 'bcrypt_sha256'

LOGIN_URL = '/login/'

try:
    from local_config import *  # noqa
except ImportError:
    pass
