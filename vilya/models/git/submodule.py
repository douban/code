# -*- coding: utf-8 -*-

from __future__ import absolute_import


class Submodule(object):

    def __init__(self, url, path):
        self._url = url
        self._path = path
        if url.find('code.dapps.douban.com/'):
            self._host = 'code'
        elif url.find('github.com/'):
            self._host = 'github'
        else:
            self._host = 'other'

    def as_dic(self):
        return {"type": "submodule",
                "url": self._url,
                "path": self._path,
                "host": self._host}
