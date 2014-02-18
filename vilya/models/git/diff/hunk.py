# -*- coding: utf-8 -*-

from __future__ import absolute_import
from ellen.utils.mdiff import hunk2
from vilya.models.consts import LINECOMMENT_INDEX_EMPTY
from vilya.models.git.diff.line import Line


class Hunk(object):

    # FIXME: old_lines/new_lines 不包含 'No newline at end of file'，导致行号对不上，也导致review评论显示不出来
    def __init__(self, patch, hunk=None, start_pos=None, **kw):
        self.patch = patch
        self._hunk = hunk  # jagare hunk
        hunk = hunk if hunk else kw
        self.old_start = hunk['old_start']
        self.new_start = hunk['new_start']
        self.old_lines = hunk['old_lines']
        self.new_lines = hunk['new_lines']
        self._start_pos = start_pos  # position in this patch
        self._top_contexts = []
        self._bottom_contexts = []
        self.skipped_old_start = kw.get('skipped_old_start', 0)
        self.skipped_new_start = kw.get('skipped_new_start', 0)
        self.skipped_old_end = kw.get('skipped_old_end', 0)
        self.skipped_new_end = kw.get('skipped_new_end', 0)
        self._top_contexts += kw.get('contexts', [])

    @property
    def start_pos(self):
        return self._start_pos

    @start_pos.setter
    def start_pos(self, value):
        self._start_pos = value

    @property
    def n_lines(self):
        return self.old_lines + self.new_lines

    @property
    def old_end(self):
        return self.old_start + self.old_lines - 1

    @property
    def new_end(self):
        return self.new_start + self.new_lines - 1

    def expand_top_contexts(self, contexts):
        self._top_contexts[:0] = contexts
        n = len(contexts)
        self.old_start -= n
        self.new_start -= n
        self.old_lines += n
        self.new_lines += n

    def expand_bottom_contexts(self, contexts):
        self._bottom_contexts += contexts
        n = len(contexts)
        self.old_lines += n
        self.new_lines += n

    @property
    def heading(self):
        line_text = '@@ -%s,%s +%s,%s @@' % (self.old_start,
                                             self.old_lines,
                                             self.new_start,
                                             self.new_lines)
        old = None
        new = None
        attr = ' '
        _line = Line(self, old, new, self.start_pos, line_text, attr)
        return _line

    def mdiff(self, side_by_side=None):
        ''' return lines(attr, line_text) '''
        if not self._hunk:
            return []
        return hunk2(self._hunk['lines'], self._hunk['mdiff'], side_by_side=side_by_side)

    # no use yet
    #def _get_old_text(self):
    #    out = []
    #    for (attr, line_text) in self.lines:
    #        if attr != '+':
    #            out.append(line_text)
    #    return out

    #def _get_new_text(self):
    #    out = []
    #    for (attr, line_text) in self.lines:
    #        if attr != '-':
    #            out.append(line_text)
    #    return out

    # GIT_DIFF_LINE_CONTEXT   = ' ',
    # GIT_DIFF_LINE_ADDITION  = '+',
    # GIT_DIFF_LINE_DELETION  = '-',
    # GIT_DIFF_LINE_CONTEXT_EOFNL = '=', Both files have no LF at end
    # GIT_DIFF_LINE_ADD_EOFNL = '>', Old has no LF at end, new does
    # GIT_DIFF_LINE_DEL_EOFNL = '<', Old has LF at end, new does not

    def _side_lines(self, side=None):
        def filter_linecomments(_line):
            #index = _line.linenum if self.patch.has_linenum else _line.pos_in_patch
            #linecomments = self.patch.comment_groups.get(index, [])
            linecomments = []
            comments_by_line = self.patch.comments_by_line.get(_line.linenum)
            comments_by_pos = self.patch.comments_by_pos.get(_line.pos_in_patch)
            if comments_by_line:
                linecomments += comments_by_line
            if comments_by_pos:
                linecomments += comments_by_pos
            return linecomments

        old_num = self.old_start
        new_num = self.new_start
        pos = self.start_pos + 1  # +1 means skip hunk_heading

        if self._top_contexts:
            for line_text in self._top_contexts:
                _line = Line(self, old_num, new_num, pos, ' %s' % line_text, ' ')
                old_num += 1
                new_num += 1
                pos += 1
                _line.linecomments = filter_linecomments(_line)
                yield _line

        for (attr, line_text) in self.mdiff(side_by_side=side):
            _line = Line(self, old_num, new_num, pos, line_text, attr)
            pos += 1
            if not attr:
                _line.old = None
                _line.new = None
            elif attr == '+' or attr == '<':
                new_num += 1
                _line.old = None
            elif attr == '-' or attr == '>':
                old_num += 1
                _line.new = None
            else:
                old_num += 1
                new_num += 1
            _line.linecomments = filter_linecomments(_line)
            yield _line

        if self._bottom_contexts:
            for line_text in self._bottom_contexts:
                _line = Line(self, old_num, new_num, pos, ' %s' % line_text, ' ')
                old_num += 1
                new_num += 1
                pos += 1
                _line.linecomments = filter_linecomments(_line)
                yield _line

    # 暂时没用
    #def _side_lines2(self, side=None):
    #    old_num = self.old_start
    #    new_num = self.new_start
    #    for (old_attr, old_line, new_attr, new_line) in self.mdiff(side_by_side=side):
    #        _old_line = Line(old_num, None, old_line, old_attr)
    #        _new_line = Line(None, new_num, new_line, new_attr)
    #        if old_attr == '+' or old_attr == '-':
    #            old_num += 1
    #        elif new_attr == '+' or new_attr == '-':
    #            new_num += 1
    #        else:
    #            new_num += 1
    #            old_num += 1
    #        yield (_old_line, _new_line)

    @property
    def lines(self):
        return self._side_lines()

    def side_lines(self, side='old'):
        return self._side_lines(side=side)

    def contain(self, linenum):
        # FIXME: 暂时 +1 判断 old_end/new_end
        old, new = linenum
        if old != LINECOMMENT_INDEX_EMPTY:
            return self.old_start <= old and old <= self.old_end + 1
        if new != LINECOMMENT_INDEX_EMPTY:
            return self.new_start <= new and new <= self.new_end + 1
        return False
