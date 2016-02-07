# -*- coding: utf-8 -*-
import urllib
import hashlib


def gravatar_url(email, size=80):
    # 线上尺寸图已有size: (48, 64, 80)
    default = "http://www.gravatar.com/avatar"
    url = "http://www.gravatar.com/avatar/" + hashlib.md5(
        email.encode('utf8').lower()).hexdigest() + "?"
    url += urllib.urlencode({'d': default, 's': str(size), 'r': 'x'})
    return url
