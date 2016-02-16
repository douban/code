# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth.models import User


class Project(models.Model):

    # TODO(xutao) name regex
    name = models.CharField(max_length=100)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    desc = models.CharField(max_length=255)
    path = models.CharField(max_length=100)
    full_name = models.CharField(max_length=70)
    created_at = models.DateTimeField('created at', auto_now_add=True)
    updated_at = models.DateTimeField('updated at', auto_now=True)

    def __str__(self):
        return self.full_name

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, Project) and self.id == other.id

    def __ne__(self, other):
        return not self.__eq__(other)
