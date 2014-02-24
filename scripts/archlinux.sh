#!/usr/bin/env bash                                                                                                 

#Get generic function                                                                                                 
. common.sh

echo "Install needed package.This may take some time..."
sudo pacman -S git gcc make python2-pip python2-virtualenv memcached git --noconfirm -q

echo "Install mysql..."
sudo pacman -S mysql --noconfirm -q
sudo systemctl start mysqld

echo "Setup memcached port to 11311..."
sudo sed -i "s/memcached -l/memcached -p 11311 -l/" /usr/lib/systemd/system/memcached.service
sudo systemctl start memcached

echo "Install libmemcached..."
install_libmemcached

# Use virtualenv2
sudo mv /usr/bin/virtualenv /usr/bin/virtualenv.bak
sudo ln -s /usr/bin/virtualenv2 /usr/bin/virtualenv

echo "Install code..."
install_code

echo "Start app..."
start_app
