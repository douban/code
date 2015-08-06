#!/usr/bin/env bash

#Get generic function
. common.sh

echo "Install needed package.This may take some time..."
sudo yum install -y -q git python-virtualenv python-devel memcached gcc gcc-c++

echo "Install mysql..."
sudo yum install -y -q mysql-server mysql mysql-devel
sudo /etc/init.d/mysqld start

echo "Setup memcached port to 11311..."
sudo sed -i "s/PORT=11211/PORT=11311/" /etc/init.d/memcached
sudo /etc/init.d/memcached start

echo "Install code..."
install_code

echo "Start app..."
start_app
