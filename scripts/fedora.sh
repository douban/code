#!/usr/bin/env bash

#Get generic function
. common.sh

echo "Install needed package.This may take some time..."
sudo yum install -y -q git python-virtualenv python-devel memcached gcc gcc-c++

echo "Install mysql..."
sudo yum install mysql-server mysql
#fedora only this method
sudo service mysqld start

echo "Setup memcached port to 11311..."
sudo sed -i "s/PORT=11211/PORT=11311/" /etc/sysconfig/memcached
sudo service memcached restart

echo "Install libmemcached..."
install_libmemcached

echo "Install code..."
install_code

echo "Start app..."
start_app
