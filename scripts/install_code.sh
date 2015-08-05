#!/usr/bin/env bash

# Check Python version > 2.7
test `python -c 'import sys; print sys.version_info < (2, 7)'` = "True" && echo 'CODE requires Python 2.7.' && exit 1

url='https://raw.githubusercontent.com/douban/code/master/scripts'

if [ -f /etc/fedora-release ] ; then
    file="$url/fedora.sh"
elif [ -f /etc/redhat-release ] ; then
    file="$url/centos.sh"
elif [ -f /etc/SuSE-release ] ; then
    file="$url/opensuse.sh"
elif [ -f /etc/debian_version ] ; then
    file="$url/ubuntu.sh"
elif [ -f /etc/gentoo-release ] ; then
    file="$url/gentoo.sh"
elif [ -f /etc/arch-release ] ; then
    file="$url/archlinux.sh"
else
    echo "Not yet support the system!"
    exit 1
fi

curl -O "$url/common.sh"
bash <(curl -s $file)
rm common.sh -f
