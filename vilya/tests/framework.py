import os
import sys


TEST_DIR = os.path.dirname(os.path.realpath(__file__))
CODE_DIR = os.path.dirname(os.path.dirname(TEST_DIR))
STUB_DIR = os.path.join(TEST_DIR, 'stub')
sys.path.insert(0, STUB_DIR)
os.environ['VILYA_TEST'] = "True"

memcached = {
    'servers': [],
    'disabled': False,
}

import cmemcached
from unittest import TestCase
from vilya.libs.store import store


class VilyaTestCase(TestCase):

    def setUp(self):
        self.store = store
        self.cursor = self.store.get_cursor()
        self.cursor.delete_without_where = True
        super(VilyaTestCase, self).setUp()

    def tearDown(self):
        super(VilyaTestCase, self).tearDown()
        self.cursor.execute('truncate table projects')
        self.cursor.execute('truncate table organizations')
        self.cursor.execute('truncate table boards')
        self.cursor.execute('truncate table cards')
        self.cursor.execute('truncate table users')
        self.cursor.execute('truncate table pulls')
        self.cursor.execute('truncate table project_board_counters')
        self.cursor.execute('truncate table project_card_counters')
        self.cursor.connection.commit()
        self.store.rollback_all(force=True)
        if hasattr(cmemcached, 'clear'):
            cmemcached.clear()
