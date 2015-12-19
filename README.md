[![Build Status](https://travis-ci.org/douban/code.png?branch=master)](https://travis-ci.org/douban/code)

Douban CODE
===========

* Website: <http://douban-code.github.io>
* Guide: <http://douban-code.github.io/pages/getting-started.html>

Dependency
----------
- libmc <https://github.com/douban/libmc>
- Python 2.7+
- pip >= 1.4.1

Docker Installation
-------------------

1. Intall [Docker Engine](https://docs.docker.com/engine/installation/)
   and [Docker Compose](https://docs.docker.com/compose/install/).
2. Note the Docker host IP address, if you are using a Docker Machine VM,
   you can use the `docker-machine ip MACHINE_NAME` to get the IP address.
3. `cp code.local.env.sample code.local.env`
    then change the value of `DOUBAN_CODE_DOMAIN` to `http://IP:8200`.
4. `docker-compose build`
5. `docker-compose up -d`
6. `mysql -udouban_code -pmy-code-passwd -h IP -D valentine < vilya/databases/schema.sql`
7. open http://IP:8200

Vagrant Installation(Recommended)
--------------------

```
$cd code
$vagrant up
$vagrant ssh
# In ubuntu. we use `supervisor` to monitor and control CODE and other services.
#You just go web http://localhost:8200
```

Quick Installation
------------------
Currently supports following systems:

* gentoo
* ubuntu/debian
* centos/redhat/fedora
* opensuse
* archlinux

You only need to execute:

```
$bash <(curl -s https://raw.githubusercontent.com/douban/code/master/scripts/install_code.sh)
```

Then install & run `supervisor` to monitor and control all services of code.

```
pip install supervisor
sudo wget -O /etc/init.d/supervisor https://raw.githubusercontent.com/Supervisor/initscripts/master/ubuntu
sudo chmod +x /etc/init.d/supervisor
sudo cp scripts/supervisord.conf /etc/supervisord.conf
sudo cp scripts/code.conf /etc/supervisor/conf.d/code.conf
sudo /etc/init.d/supervisor start
# go web http://localhost:8200
```

Notes: The installation script is in `scripts` subdirectory, for example for ubuntu/debian,
you can find `scripts/ubuntu.sh`

FAQ
----

1. single http daemon
 - `gunicorn -b 127.0.0.1:8001 app:app` # git http daemon

2. vilya.config.DOMAIN
 - if you run 'gunicorn -b IP:PORT app:app', the DOMAIN should be 'http://IP:PORT'


License
-------
CODE is under Revised BSD License.
See the [LICENSE file](https://github.com/douban/code/blob/master/LICENSE) for the full license text.
