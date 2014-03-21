# coding: utf-8

import os
from os.path import dirname, abspath

DEVELOP_MODE = False


DAE_ENV = os.environ.get('DAE_ENV')
CSS_JS_DEVELOP_MODE = DAE_ENV == 'SDK'


CODE_DIR = dirname(abspath(__file__))
if os.environ.get('VILYA_TEST'):
    CODE_DIR = os.path.join(CODE_DIR, 'tests')
HOOKS_DIR = os.path.join(CODE_DIR, 'hooks')
REPO_DIR = os.path.join(CODE_DIR, 'permdir')

# session
SESSION_EXPIRE_DAYS = 14
SESSION_DOMAIN = ''
SESSION_COOKIE_NAME = 'code_user'


MEMCACHED = {
    'servers': ["127.0.0.1:11311", ],
    'new_servers': [],
    'backup_servers': [],
    'disabled': False,
    'local_cache': True,
    'log_every_actions': False,
    'slave_servers': [],
}

DOUBANDB = {
    'servers': ["127.0.0.1:11311", ],
    'proxies': []
}

REDIS = {'host': '127.0.0.1', 'port': 6379}
REDIS_STORE = {
    'shire': {
        'host': '127.0.0.1', 'port': 6379,
        'dbs': {1: 'DEFAULT', 2: 'bloomfilters'},
    },
    'counter': {
        'host': '127.0.0.1', 'port': 6379,
        'dbs': {63: 'test-counter'},
    },
}

MYSQL_STORE = {
    "farms": {
        "code_farm": {
            "master": "localhost:3306:valentine:root:",
            "tables": ["*"],
        }
    }
}

DOMAIN = "http://127.0.0.1:8000/"

MAKO_FS_CHECK = True

EMAIL_SUFFIX = 'douban.com'

try:
    from local_config import *
except ImportError:
    pass
