# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from vilya.libs.gravatar import gravatar_url
from vilya.models.inbox import Inbox


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # TODO(xutao) gravatar
    # TODO(xutao) trello token

    # TODO(xutao) team
    # TODO(xutao) project
    # TODO(xutao) notification
    # TODO(xutao) badge
    # TODO(xutao) setting

    def get_gravatar_url(self, size=80):
        return gravatar_url(self.email, size)

    @property
    def inbox(self):
        return Inbox.get(user=self.name)

    @property
    def unread_notification_count(self):
        from vilya.models.notification import Notification
        return Notification.unread_count(self.name)


class Follower(models.Model):
    follower = models.ForeignKey(User, db_constraint=False)
    followee = models.ForeignKey(User, db_constraint=False)
    created_at = models.DateTimeField('created at', auto_now_add=True)
    updated_at = models.DateTimeField('updated at', auto_now=True)


class Email(models.Model):
    user = models.ForeignKey(User, db_constraint=False)
    email = models.CharField(max_length=100)
    created_at = models.DateTimeField('created at', auto_now_add=True)
    updated_at = models.DateTimeField('updated at', auto_now=True)


class Key(models.Model):
    title = models.CharField(max_length=128)
    text = models.CharField(max_length=1024)
    fingerprint = models.CharField(max_length=48)
    user = models.ForeignKey(User, db_constraint=False)
    created_at = models.DateTimeField('created at', auto_now_add=True)
    updated_at = models.DateTimeField('updated at', auto_now=True)


# TODO(xutao) support kind for activity?
class Badge(models.Model):
    desc = models.CharField(max_length=1024)
    created_at = models.DateTimeField('created at', auto_now_add=True)
    updated_at = models.DateTimeField('updated at', auto_now=True)


class UserBadge(models.Model):
    user = models.ForeignKey(User, db_constraint=False)
    badge = models.ForeignKey(Badge, db_constraint=False)
    desc = models.CharField(max_length=1024)
    created_at = models.DateTimeField('created at', auto_now_add=True)
    updated_at = models.DateTimeField('updated at', auto_now=True)
