Douban CODE
===========

* Website: <http://douban-code.github.io>
* Guide: <http://douban-code.github.io/pages/getting-started.html>

Dependency
----------
- Python 2.7+
- pip >= 1.4.1

Prepare
-------
- mysql # default port

```
# import vilya/databases/schema.sql to database `valentine`
$ mysql -uroot -e 'create database valentine;'
$ mysql -uroot -D valentine < vilya/databases/schema.sql
```

- memcached # default port

- customize code config
```
# after clone code repo you can change the default config by:
$ cd {CODE_REPO}
$ cp vilya/local_config.py.tmpl vilya/local_config.py
# overwrite configs defined in vilya/config.py.
$ vim vilya/local_config.py
```

Getting started
---------------
Firstly install libmemcached:

http://douban-code.github.io/pages/python-libmemcached.html

Then go through the following steps:

```
git clone https://github.com/douban/code.git
cd code
mysql -uroot -e 'create database valentine;'
mysql -uroot -D valentine < vilya/databases/schema.sql
virtualenv venv
. venv/bin/activate
pip install mime python-magic
pip install cython  # should install first
pip install -U setuptools  # python-libmemcached require updated setuptools
pip install -r requirements.txt
gunicorn -w 2 -b 127.0.0.1:8000 app:app  # web & git http daemon
```

FAQ
----

1. single http daemon
 - `gunicorn -b 127.0.0.1:8001 smart_httpd:app` # git http daemon

2. vilya.config.DOMAIN
 - if you run 'gunicorn -b IP:PORT app:app', the DOMAIN should be 'http://IP:PORT/'


License
-------
See the [LICENSE file](https://github.com/douban/code/blob/master/LICENSE) for the full license text.
