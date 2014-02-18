# -*- coding: utf-8 -*-
import re


URL_RE = re.compile(
    r'^(?:http|ftp)s?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)

INTERG_RE = re.compile(r'^[1-9]\d*$')

EMAIL_RE = re.compile(r"""^([a-zA-Z0-9_\-\.]+)@
                    ((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.)|
                    (([a-zA-Z0-9\-]+\.)+))
                    ([a-zA-Z]{2,4}|[0-9]{1,3})(\]?)$""", re.VERBOSE)

USER_ID_RE = re.compile(r'^[a-zA-Z0-9_\-\.]{1,20}$')

PROJECT_NAME_RE = re.compile(r'^[a-zA-Z0-9-_]{1,75}$')


def check_name(name, field_name="Name"):
    if len(name) > 100:
        return "%s is too long" % field_name


def check_project_name(name, field_name="Project name"):
    if not PROJECT_NAME_RE.match(name):
        return "%s must match %s" % (field_name, PROJECT_NAME_RE.pattern)


def check_url(url, field_name="Url"):
    if len(url) > 1024:
        return "%s is too long" % field_name
    if not URL_RE.match(url):
        return "%s is illegal" % field_name


def check_integer(integer, field_name="ID"):
    if not INTERG_RE.match(integer.__str__()):
        return "%s is not a integer" % field_name


def check_email(email, field_name="Email"):
    if not EMAIL_RE.match(email):
        return "%s is non verified" % field_name


def check_git_url(url):
    return check_url(url)


def check_user_id(id):
    return USER_ID_RE.match(id)