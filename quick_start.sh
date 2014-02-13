#!/bin/sh

virtualenv venv
. venv/bin/activate
pip install -U setuptools
pip install cython
pip install -r requirements.txt
deactivate
. venv/bin/activate
gunicorn -b 0.0.0.0:8000 app:app
