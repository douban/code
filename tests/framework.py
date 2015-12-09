import os
import sys


TEST_DIR = os.path.dirname(os.path.realpath(__file__))
CODE_DIR = os.path.dirname(os.path.dirname(TEST_DIR))
STUB_DIR = os.path.join(TEST_DIR, 'stub')
sys.path.insert(0, STUB_DIR)

memcached = {
    'servers': [],
    'disabled': False,
}

import cmemcached
