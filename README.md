Douban CODE
===========

* Website: <http://douban-code.github.io>
* Guide: <http://douban-code.github.io/pages/getting-started.html>

Dependency
----------
- libmemcached <http://douban-code.github.io/pages/python-libmemcached.html>
- Python 2.7+
- pip >= 1.4.1

Quick Installation
------------------
Currently supports the following systems:

* gentoo
* ubuntu/debian
* centos/redhat/fedora
* opensuse
* archlinux

You only to excute:

```
bash <(curl -s https://raw.github.com/douban/code/master/scripts/install_code.sh)
```

Notes: The install script in `code/scripts` subdirectory, for example ubuntu/debian,
You can see `code/scripts/ubuntu.sh`

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
```
git clone https://github.com/douban/code.git
cd code
mysql -uroot -e 'create database valentine;'
mysql -uroot -D valentine < vilya/databases/schema.sql
virtualenv venv
. venv/bin/activate
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
CODE is under Revised BSD License.
See the [LICENSE file](https://github.com/douban/code/blob/master/LICENSE) for the full license text.
