# coding: utf-8

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


MEMCACHED_HOSTS = ['127.0.0.1:11311']
MEMCACHED_CONFIG = {
    'do_split': True,
    'comp_threshold': 0,
    'noreply': False,
    'prefix': None,
    'hash_fn': MC_HASH_MD5,
    'failover': False
}

DOUBANDB = {
    'servers': ["127.0.0.1:11311", ],
    'proxies': []
}

MYSQL_STORE = {
    "farms": {
        "code_farm": {
            "master": "localhost:3306:valentine:root:",
            "tables": ["*"],
        }
    }
}

REDIS_URI = 'redis://localhost:6379/0'

BEANSDBCFG = {
    "localhost:7901": range(16),
    "localhost:7902": range(16),
    "localhost:7903": range(16),
}

DOMAIN = 'http://127.0.0.1:8200/'
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

try:
    from local_config import *  # noqa
except ImportError:
    pass
