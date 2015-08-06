#!/usr/bin/env bash

#Get generic function
. common.sh

echo "Install needed package.This may take some time..."
sudo apt-get install build-essential g++ git python-pip python-virtualenv python-dev memcached -yq

echo "Install mysql..."
sudo apt-get install mysql-client mysql-server libmysqlclient-dev -yq
/etc/init.d/mysql restart

echo "Setup memcached port to 11311..."
sudo sed -i "s/11211/11311/g" /etc/memcached.conf
sudo /etc/init.d/memcached restart

echo "Install code..."
install_code

echo "Start app..."
start_app
