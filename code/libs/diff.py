# -*- coding: utf-8 -*-
from difflib import _mdiff as mdiff  # noqa


def _get_hunk(lines):
    new, old = [], []
    for attr, line in lines:
        if attr != 'other':
            if attr != 'add':
                old.append(attr)
            if attr != 'rem':
                new.append(attr)
    return new, old


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
    new, old = _get_hunk(a_hunk)
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
        del_code, add_code, rep_code, color_code = match.groups()
        if del_code:
            return self.span(del_code, "x")
        elif add_code:
            return self.span(add_code, "i")
        elif rep_code:
            return self.span(rep_code, "c")
        elif color_code:
            color_code = re.sub(r'[\+\-\^](.*?)', r'\1', color_code)
            return self.span(color_code, "color")

    def span(self, code, cls):
        text = html_quote(str(code))
        return '<span class="%s">%s</span>' % (cls, text)

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
