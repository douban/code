#!/bin/bash

echo "drop database if exists valentine" | mysql
echo "create database valentine" | mysql
if [ $? -ne 0 ]; then
    echo "create database valentine" | mysql -uroot -p
fi
(echo "use valentine"; cat code/databases/schema.sql) | mysql
