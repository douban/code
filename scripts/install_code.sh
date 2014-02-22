#!/usr/bin/env bash

url='https://raw.github.com/dongweiming/code/master/scripts'

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
else
    echo "Do not support the system!"
    exit 1
fi

curl -O "$url/common.sh"
bash <(curl -s $file)
rm common.sh -f
