# -*- coding: utf-8 -*-
from urllib import urlencode


def redirect_to_login(request, next_path, login_url, redirect_field_name):
    url = login_url + '?' + urlencode({redirect_field_name: next_path})
    return request.redirect(url)
