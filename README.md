Douban CODE
===========

* Website: <http://douban-code.github.io>

Prepare
-------
- mysql # default port

```
# import code/databases/schema.sql to database `valentine`
$ mysql -uroot -e 'create database valentine;'
$ mysql -uroot -D valentine < code/databases/schema.sql
```

- memcached # default port


Getting started
---------------
- `virtualenv venv`
- `. venv/bin/activate`
- `pip install cython` # should install first
- `pip install -U setuptools` # python-libmemcached require updated setuptools
- `pip install -r requirements.txt`
- `gunicorn -b 127.0.0.1:8000 app:app` # web & git http daemon


FAQ
----

1. single http daemon
 - `gunicorn -b 127.0.0.1:8001 smart_httpd:app` # git http daemon


License
-------
See the LICENSE file for the full license text.
