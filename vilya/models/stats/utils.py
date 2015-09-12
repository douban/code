# -*- coding: utf-8 -*-
from consts import conf


def getcommitrange(defaultrange='HEAD', end=None, end_only=False):
    if end:
        return (defaultrange, end)
    if len(conf['commit_end']) > 0:
        if end_only or len(conf['commit_begin']) == 0:
            return (conf['commit_end'], None)
        return (conf['commit_end'], conf['commit_begin'])
    return (defaultrange, None)


def getkeyssortedbyvalues(dict):
    return map(lambda el: el[1], sorted(map(
        lambda el: (el[1], el[0]), dict.items())))


def getkeyssortedbyvaluekey(d, key):
    return map(lambda el: el[1], sorted(map(
        lambda el: (d[el][key], el), d.keys())))
