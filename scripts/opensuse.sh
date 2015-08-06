#!/usr/bin/env bash

#Get generic function
. common.sh

echo "Install needed package.This may take some time..."
sudo zypper -nq install gcc gcc-c++ python-pip python-virtualenv git memcached python-devel make

echo "Install mysql..."
# After 12.3 mysql is mariadb
sudo zypper -nq install mysql libmysqlclient-devel
sudo /sbin/service mysql start

echo "Setup memcached port to 11311..."
sudo sed -i 's/MEMCACHED_PARAMS=\"/MEMCACHED_PARAMS=\"-p 11311 /' /etc/sysconfig/memcached
sudo /etc/init.d/memcached restart

echo "Install code..."
install_code

echo "Start app..."
start_app
