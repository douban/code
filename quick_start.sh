#!/bin/sh

echo "Setup database..."
. ./setup_databases.sh

echo "Init virtualenv..."
virtualenv venv
. venv/bin/activate
pip install -U setuptools
pip install cython
pip install -r requirements.txt

echo "Start serveing!!!"
echo
echo
deactivate
. venv/bin/activate
gunicorn -b 0.0.0.0:8000 app:app
