# coding=utf-8
from celery import Celery

app = Celery()
app.config_from_object('celeryconfig')


def async(func):
    def deco_(*args, **kwargs):
        return app.task(func).apply_async(*args, **kwargs)
    return deco_
