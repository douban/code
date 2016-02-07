# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from vilya.libs.gravatar import gravatar_url


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.CharField(max_length=100)

    # TODO(xutao) gravatar
    # TODO(xutao) trello token

    # TODO(xutao) team
    # TODO(xutao) project
    # TODO(xutao) notification
    # TODO(xutao) badge
    # TODO(xutao) setting

    def get_gravatar_url(self, size=80):
        return gravatar_url(self.email, size)
