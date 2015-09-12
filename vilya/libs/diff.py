# -*- coding: utf-8 -*-
import re
import difflib
from quixote.html import html_quote


def _get_old(lines):
    return [line for (attr, line) in lines if attr not in ('add', 'other')]


def _get_new(lines):
    return [line for (attr, line) in lines if attr not in ('rem', 'other')]


def mdiff(old, new):
    return difflib._mdiff(old, new)


def rediff(generator):
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
                yield (('l', 'emp', ' '), ('r', 'add', line))
            elif not new[0]:
                line = old[1].strip('\x00\x01')
                yield (('l', 'rem', line), ('r', 'emp', ' '))
            else:
                #mix
                yield (('l', 'rem', '-' + old[1]), ('r', 'add', '+' + new[1]))
        else:
            yield (('l', 'normal', ' ' + old[1]),
                   ('r', 'normal', ' ' + old[1]))


def rehunk(a_hunk, side=False):
    old = _get_old(a_hunk)
    new = _get_new(a_hunk)
    if side:
        hunk = sidediff(mdiff(old, new))
    else:
        hunk = rediff(mdiff(old, new))
    return list(hunk)


class LineHtmlPlugin(object):
    def __init__(self, name, regex, left_html, right_html,
                 left_trim='', right_trim=''):
        self.name = name
        self.regex = regex
        self.left_html = left_html
        self.right_html = right_html
        self.left_trim = left_trim
        self.right_trim = right_trim

        self.left_len = len(left_trim)
        self.right_len = len(right_trim)

        self.init()

    def init(self, len_s=0):
        self.pairs = []
        self._idx_mapping_counter = {i: 1 for i in range(len_s + 1)}

    def add_pair(self, start, end, match):
        piece = match.group(0)

        left_html = (self.left_html(match)
                     if callable(self.left_html) else self.left_html)
        right_html = (self.right_html(match)
                      if callable(self.right_html) else self.right_html)

        self.pairs.append(dict(start=start,
                               end=end,
                               left_html=left_html,
                               right_html=right_html))

        self.idx_shift(start + self.left_len, self.left_len)
        self.idx_shift(end, self.right_len)

        return self._trim(piece)

    @property
    def idx_mapping(self):
        _idx_mapping = {}
        for i, v in self._idx_mapping_counter.items():
            last_idx_value = -1 if i == 0 else _idx_mapping[i - 1]
            _idx_mapping[i] = last_idx_value + v
        return _idx_mapping

    def idx_shift(self, idx, value):
        """idx_mapping 从 idx 开始向左移动 value 个位置"""
        self._idx_mapping_counter[idx] -= value

    def _trim(self, s):
        if self.right_len == 0:
            return s[self.left_len:]
        else:
            return s[self.left_len:-self.right_len]


class LineHtml(object):
    """render internal diff"""

    def __init__(self, plugins=None):
        self.s = None
        self.plugins = plugins

    def run_plugins(self):
        for plugin in self.plugins:
            plugin.init(len(self.s))

            tmp = ''
            last_end = 0
            for match in plugin.regex.finditer(self.s):

                start, end = match.span()
                tmp += self.s[last_end:start]

                tmp += plugin.add_pair(start, end, match)

                last_end = end
            self.s = tmp + self.s[last_end:]

    def collect_pairs(self):
        pairs = []
        for plugin in self.plugins:
            idx_mapping = plugin.idx_mapping
            pairs.extend(plugin.pairs)
            for pair in pairs:
                pair['start'] = idx_mapping[pair['start']]
                pair['end'] = idx_mapping[pair['end']]

    def decross_pairs(self):
        """去交叉"""
        for i_plugin, pair in [(i, pair)
                               for i, plugin in enumerate(self.plugins)
                               for pair in plugin.pairs]:
            for p, plugin in [(pair2, plugin2)
                              for plugin2 in self.plugins[:i_plugin]
                              for pair2 in plugin2.pairs]:
                # pair 跟 p 交叉，因为 pair 是后覆盖上去的，p 被分为两部分
                if (p['start'] < pair['start']
                        and pair['start'] < p['end']
                        and p['end'] < pair['end']):
                    plugin.pairs.remove(p)
                    plugin.pairs.append(dict(start=p['start'],
                                             end=pair['start'],
                                             left_html=p['left_html'],
                                             right_html=p['right_html']))
                    plugin.pairs.append(dict(start=pair['start'],
                                             end=p['end'],
                                             left_html=p['left_html'],
                                             right_html=p['right_html']))
                elif (pair['start'] < p['start']
                        and p['start'] < pair['end']
                        and pair['end'] < p['end']):
                    plugin.pairs.remove(p)
                    plugin.pairs.append(dict(start=p['start'],
                                             end=pair['end'],
                                             left_html=p['left_html'],
                                             right_html=p['right_html']))
                    plugin.pairs.append(dict(start=pair['end'],
                                             end=p['end'],
                                             left_html=p['left_html'],
                                             right_html=p['right_html']))

    def merge_pairs(self):
        left_html_by_idx = {}
        right_html_by_idx = {}
        for plugin in self.plugins:
            for pair in plugin.pairs:
                start = pair['start']
                end = pair['end']
                left_html = pair['left_html']
                right_html = pair['right_html']
                left_html_by_idx[start] = (left_html + left_html_by_idx[start]
                                           if start in left_html_by_idx
                                           else left_html)
                right_html_by_idx[end] = (right_html_by_idx[end] + right_html
                                          if end in right_html_by_idx
                                          else right_html)
        html_by_idx = {}
        for i, left_html in left_html_by_idx.items():
            if i in right_html_by_idx:
                right_html = right_html_by_idx[i]
                html_by_idx[i] = right_html + left_html
        html_by_idx.update({k: v for k, v in left_html_by_idx.iteritems()
                           if k not in html_by_idx})
        html_by_idx.update({k: v for k, v in right_html_by_idx.iteritems()
                           if k not in html_by_idx})
        return html_by_idx

    def __call__(self, s):
        if not s:
            return ''
        self.s = str(s)

        self.run_plugins()
        self.collect_pairs()
        self.decross_pairs()
        html_by_idx = self.merge_pairs()

        parts = []
        last_end = 0
        for i in sorted(html_by_idx):
            html = html_by_idx[i]
            parts.append(html_quote(self.s[last_end:i]))
            parts.append(html)
            last_end = i

        parts.append(html_quote(self.s[last_end:]))
        self.s = ''.join(parts)

        return self.s

linehtml = LineHtml(plugins=[
    LineHtmlPlugin('del_code',
                   re.compile(ur'\x00\-(.*?)\x01', re.UNICODE + re.DOTALL),
                   '<span class="d">', '</span>',
                   left_trim=u'\x00-', right_trim=u'\x01'),
    LineHtmlPlugin('add_code',
                   re.compile(ur'\x00\+(.*?)\x01', re.UNICODE + re.DOTALL),
                   '<span class="i">', '</span>',
                   left_trim=u'\x00+', right_trim=u'\x01'),
    LineHtmlPlugin('rep_code',
                   re.compile(ur'\x00\^(.*?)\x01', re.UNICODE + re.DOTALL),
                   '<span class="c">', '</span>',
                   left_trim=u'\x00^', right_trim=u'\x01'),
    LineHtmlPlugin('color_code',
                   re.compile(ur'#[A-Fa-f0-9]{3,6}', re.UNICODE),
                   lambda match: ('<span class="color" data-color="%s">'
                                  % match.group(0)),
                   '</span>'),
])
