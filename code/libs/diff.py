# -*- coding: utf-8 -*-
import difflib


def _get_old(lines):
    return [line for (attr, line) in lines if attr not in ('add', 'other')]


def _get_new(lines):
    return [line for (attr, line) in lines if attr not in ('rem', 'other')]


def mdiff(old, new):
    return difflib._mdiff(old, new)


def rediff(generator):
    change = False
    temp = []
    for old, new, changed in generator:
        if changed:
            if not old[0]:
                line = new[1].strip('\x00\x01')
                temp.append(('add', line))
            elif not new[0]:
                line = old[1].strip('\x00\x01')
                yield ('rem', line)
            else:
                #mix
                yield ('rem', '-' + old[1])
                temp.append(('add', '+' + new[1]))
        else:
            for t in temp:
                yield t
            temp = []
            yield ('idem', ' ' + old[1])
    if temp:
        for t in temp:
            yield t


def sidediff(generator):
    for old, new, changed in generator:
        if changed:
            if not old[0]:
                line = new[1].strip('\x00\x01')
                yield (('l', 'emp', ' '),('r', 'add', line))
            elif not new[0]:
                line = old[1].strip('\x00\x01')
                yield (('l', 'rem', line), ('r', 'emp', ' '))
            else:
                #mix
                yield (('l', 'rem', '-'+old[1]),('r', 'add', '+'+new[1]))
        else:
            yield (('l', 'normal', ' '+old[1]), ('r', 'normal', ' '+old[1]))


def rehunk(a_hunk, side=False):
    old = _get_old(a_hunk)
    new = _get_new(a_hunk)
    if side:
        hunk = sidediff(mdiff(old, new))
    else:
        hunk = rediff(mdiff(old, new))
    return list(hunk)

import re
from quixote.html import html_quote

SEQUENCE_TAGS = [
    ur'\x00\-(.*?)\x01',
    ur'\x00\+(.*?)\x01',
    ur'\x00\^(.*?)\x01',
    ur'(#[A-Fa-f0-9\x00\x01\-\+\^]{3,9})',
]

SEQUENCE_RE = re.compile("|".join(SEQUENCE_TAGS), re.UNICODE + re.DOTALL)


class LineHtml(object):

    def __init__(self):
        self.s = None

    def repl(self, match):
        ret = ""
        text = ""
        del_code = match.group(1)
        add_code = match.group(2)
        rep_code = match.group(3)
        color_code = match.group(4)
        if del_code:
            text = html_quote(str(del_code))
            ret = '<span class="x">%s</span>' % text
        elif add_code:
            text = html_quote(str(add_code))
            ret = '<span class="i">%s</span>' % text
        elif rep_code:
            text = html_quote(str(rep_code))
            ret = '<span class="c">%s</span>' % text
        elif color_code:
            color_code = re.sub(r'[\+\-\^](.*?)', r'\1', color_code)
            text = html_quote(str(color_code))
            ret = '<span class="color">%s</span>' % text
        return str(ret)

    def __call__(self, s):
        if not s:
            return ''
        self.s = s
        r = ""
        b = 0
        e = 0
        for i in SEQUENCE_RE.finditer(s):
            b, e1 = i.span()
            r += html_quote(str(s[e:b]))
            r += self.repl(i)
            e = e1
        r += html_quote(str(s[e:]))
        return r

linehtml = LineHtml()
