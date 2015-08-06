#!/usr/bin/env bash

# Use ebegin
if [ -e /lib/rc/bin/ebegin ];then
    echo=/lib/rc/bin/ebegin
    end="/lib/rc/bin/eend $?"
else
    echo=echo
    end=echo
fi
#Get generic function
. common.sh

$echo "eselect python 2.7"
sudo eselect python set 1
$end

$echo "Install needed package.This may take some time..."
sudo emerge git dev-python/pip  dev-python/virtualenv memcached -q
$end

$echo "Install mysql..."
sudo emerge mysql -q
sudo /usr/bin/mysql_install_db
sudo /etc/init.d/mysql start
$end

$echo "Setup memcached port to 11311..."
sudo sed -i 's/PORT=\"11211\"/PORT=\"11311\"/g' /etc/conf.d/memcached
sudo /etc/init.d/memcached restart
$end

$echo "Install code..."
install_code
$end

$echo "Start app..."
start_app
