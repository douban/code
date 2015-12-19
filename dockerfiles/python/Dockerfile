FROM python:2.7

ENV PYTHONUNBUFFERED 1

RUN mkdir /code \
        /pip-src
WORKDIR /code
ADD requirements.txt /code/requirements.txt

RUN pip install cython \
    && pip install -r requirements.txt --src=/pip-src
