# -*- coding: utf-8 -*-

from __future__ import absolute_import
from collections import OrderedDict


class Blob(object):
    ''' Wrapper of Jagare/pygit2 Blob.
    > A blob is just a raw byte string.
    They are the Git equivalent to files in a filesystem. '''

    def __init__(self, repo, blob):
        self.repo = repo
        self._blob = blob
        self.sha = blob['sha']
        self.data = blob['data']
        self.size = blob['size']
        self.type = blob['type']
        self.binary = blob['binary']

    def as_dict(self):
        d = OrderedDict([
            ("sha", self.sha),
            ("binary", self.binary),
            ("data", self.data if not self.binary else ''),
            ("size", self.size),
        ])
        return d

