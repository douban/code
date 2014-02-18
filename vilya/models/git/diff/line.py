# -*- coding: utf-8 -*-

from __future__ import absolute_import
from vilya.models.consts import LINECOMMENT_INDEX_EMPTY

MAX_REVIEW_CODE_LINES = 20


class LineBase(object):
    def __init__(self, old, new, text, attr=' ',
                 old_file_path=None, new_file_path=None):
        self.old = old
        self.new = new
        self.text = text
        self.attr = attr
        self.old_file_path = old_file_path
        self.new_file_path = new_file_path
        self.linecomments = None

    @property
    def linenum(self):
        return (self.old if self.old else LINECOMMENT_INDEX_EMPTY,
                self.new if self.new else LINECOMMENT_INDEX_EMPTY)


class Line(LineBase):

    def __init__(self, hunk, old, new, pos_in_patch, text, attr,
                 linecomments=[]):
        super(Line, self).__init__(old, new, text, attr)
        self.hunk = hunk
        self.pos_in_patch = pos_in_patch
        # 维护 file_path，或者 anchor
        self.old_file_path = self.hunk.patch.old_file_path
        self.new_file_path = self.hunk.patch.new_file_path
        self.linecomments = linecomments

    @property
    def review_skip_lines(self):
        ''' number of skip lines from hunk_heading to this line '''
        lines_before = self.pos_in_patch - self.hunk.start_pos
        skip_lines = (0 if lines_before < MAX_REVIEW_CODE_LINES
                      else lines_before - MAX_REVIEW_CODE_LINES)
        return skip_lines

    @property
    def review_heading(self):
        return self.review_skip_lines == 0

    @property
    def review_lines(self):
        skip_lines = self.review_skip_lines
        for idx, line in enumerate(self.hunk.lines):
            if idx < skip_lines:
                continue
            if line.pos_in_patch > self.pos_in_patch + 2:
                break
            yield line
