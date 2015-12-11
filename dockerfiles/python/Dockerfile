FROM python:2.7

RUN mkdir /code
RUN mkdir /pip-src
WORKDIR /code
ADD requirements.txt /code/requirements.txt

RUN pip install cython
RUN pip install -r requirements.txt --src=/pip-src
