# -*- coding: utf-8 -*-

from tests.base import TestCase


def test_simple_assert():
    assert True


class TestTestClass(object):
    def test_simple_assert(self):
        assert True


def test_connect_db():
    from vilya.libs.store import connect_mysql
    conn = connect_mysql()
    cursor = conn.cursor()
    cursor.execute("select * from codedouban_hooks")
    r = cursor.fetchone()
    assert r is None, "unittest database should not have rows"


class TestDb(TestCase):
    def test_insert_into_db(self):
        from vilya.libs.store import connect_mysql
        conn = connect_mysql()
        cursor = conn.cursor()
        cursor.execute("select * from codedouban_hooks")
        assert cursor.fetchall() == ()
        ok = cursor.execute(
            "insert into codedouban_hooks (project_id, url) values "
            "(1, 'test')")
        assert ok
        conn.commit()
        cursor.execute("select * from codedouban_hooks")
        assert len(cursor.fetchall()) == 1
        cursor.execute("delete from codedouban_hooks")
        conn.commit()

    def test_mc(self):
        from vilya.libs.store import get_mc
        mc = get_mc()
        key = "RANDOM________2f3fddd4455"
        assert mc.get(key) is None, "Cache should be empty after next run"
        mc.set(key, 'a value')
        assert mc.get(key) == 'a value'

    def test_mc_called_twice(self):
        from vilya.libs.store import get_mc
        mc = get_mc()
        key = "RANDOM________2f3fddd4455"
        assert mc.get(key) is None
        mc.set(key, 'a value')
        assert mc.get(key) == 'a value'
        mc2 = get_mc()
        assert mc2.get(key) == 'a value'

    def test_mc_with_strange_key_using_quote(self):
        from vilya.libs.store import get_mc
        import urllib
        mc = get_mc()
        key = urllib.quote_plus('sss sés你好的de')
        assert mc.get(key) is None, "Cache should be empty after next run"
        mc.set(key, 'a value')
        assert mc.get(key) == 'a value'

    def test_cache_decorator(self):
        from vilya.libs.store import cache
        cache_key = 'K2000'

        @cache(cache_key)
        def check():
            check.count += 1
            return True  # Shit, cannot return None here!
        check.count = 0
        assert check.count == 0
        check()
        assert check.count == 1, "Should go inside cached function once"
        [check() for i in range(10)]
        assert check.count == 1, "Should go inside cached function ONLY once"

    def test_cache_decorator_with_params(self):
        from vilya.libs.store import cache
        cache_key = 'K2000 p1:%s:%s'

        @cache(cache_key % ('{param1}', '{param2}'))
        def check(param1, param2):
            check.count += 1
            return True  # Shit, cannot return None here!
        check.count = 0
        check(1, 2)
        assert check.count == 1
        check(1, 2)
        assert check.count == 1
        check(2, 1)
        assert check.count == 2
        check(2, 1)
        assert check.count == 2
        check(1, 2)
        assert check.count == 2
        check(1, 3)
        assert check.count == 3
