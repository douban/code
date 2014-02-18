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
# import code/databases/schema.sql to database `valentine`
$ mysql -uroot -e 'create database valentine;'
$ mysql -uroot -D valentine < code/databases/schema.sql
```

- memcached # default port

- customize code config
```
# after clone code repo you can change the default config by:
$ touch CODE_REPO/code/local_config.py
# overwrite configs defined in code/config.py.
$ vim CODE_REPO/code/local_config.py
```

- install libmemcached(for ubuntu)

```
sudo apt-get install build-essential g++
wget https://launchpad.net/libmemcached/1.0/1.0.18/+download/libmemcached-1.0.18.tar.gz
git clone https://github.com/douban/python-libmemcached
tar zxf libmemcached-1.0.18.tar.gz
cd libmemcached-1.0.18
patch -p1 < ../python-libmemcached/patches/1.0/behavior.patch
patch -p1 < ../python-libmemcached/patches/1.0/empty_string.patch 
patch -p1 < ../python-libmemcached/patches/1.0/touch_expire-1.0.patch
./configure && make && sudo make install
cd ..
rm -rf python-libmemcached
rm -rf libmemcached*
sudo ldconfig
```

Getting started
---------------

```
git clone https://github.com/douban/code.git
cd code
mysql -uroot -e 'create database valentine;'
mysql -uroot -D valentine < code/databases/schema.sql
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

2. code.config.DOMAIN
 - if you run 'gunicorn -b IP:PORT app:app', the DOMAIN should be 'http://IP:PORT/'


License
-------
See the [LICENSE file](https://github.com/douban/code/blob/master/LICENSE) for the full license text.
