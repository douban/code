# -*- coding: utf-8 -*-

from __future__ import absolute_import


class Tree(object):

    def __init__(self, repo, tree):
        self.repo = repo
        self._tree = tree
        self.type = 'tree'
        self.entries = tree
        self.index = 0
        self.length = len(tree)

    def __iter__(self):
        return Tree(self.repo, self._tree)

    def next(self):
        if self.index == self.length:
            raise StopIteration
        entry = self.entries[self.index]
        self.index = self.index + 1
        return entry
