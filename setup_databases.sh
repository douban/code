#!/bin/bash
read -p "Please input Mysql User(default is root):" user
if [ "${user}" = "" ];then
    user="root"
fi
read -p "Please input Mysql ${user}'s password(default is ''):" passwd
echo "drop database if exists valentine" | mysql --user=${user} --password=${passwd}
echo "create database valentine" | mysql --user=${user} --password=${passwd}
if [ $? -ne 0 ]; then
    echo "create database valentine" | mysql --user=${user} --password=${passwd}
fi
(echo "use valentine"; cat code/databases/schema.sql) | mysql --user=${user} --password=${passwd}
