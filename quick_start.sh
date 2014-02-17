#!/bin/bash

echo "Setup database..."
. ./setup_databases.sh

echo "Init virtualenv..."
which virtualenv > /dev/null 2>&1
if [ $? != 0 ];then
    echo "Install virtualenv..."
    pip install virtualenv
fi
virtualenv venv
. venv/bin/activate
pip install -U setuptools
pip install cython

which mysql_config > /dev/null 2>&1
if [ $? != 0 ];then
    echo "mysql_config: command not found, must install it!"
    exit 1
fi
pip install -r requirements.txt

echo "Start serveing!!!"
echo
echo
gunicorn -w 2 -b 0.0.0.0:8000 app:app
