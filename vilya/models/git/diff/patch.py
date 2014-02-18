# -*- coding: utf-8 -*-

from __future__ import absolute_import
from itertools import groupby
from vilya.libs.text import is_image
from vilya.libs.generated import Generated
from vilya.models.consts import LINECOMMENT_INDEX_EMPTY
from vilya.models.git.diff.hunk import Hunk

MAX_PATCH_MOD_LINES = 2000
INVALID_OID = b'0' * 40


class Patch(object):
    # libgit2 status definition
    ## GIT_DELTA_ADDED:     code = 'A'
    ## GIT_DELTA_DELETED:   code = 'D'
    ## GIT_DELTA_MODIFIED:  code = 'M'
    ## GIT_DELTA_RENAMED:   code = 'R'
    ## GIT_DELTA_COPIED:    code = 'C'
    ## GIT_DELTA_IGNORED:   code = 'I'
    ## GIT_DELTA_UNTRACKED: code = '?'
    ## default:             code = ' '

    def __init__(self, repo, diff, patch, linecomments=[], is_limit_lines=True):
        self.repo = repo
        self.diff = diff
        self._patch = patch
        self._old_file_length = None
        self._new_file_length = None
        # patch sha == diff sha
        # FIXME: commit diff old_sha 貌似为 None
        self.old_sha = patch['old_sha']
        self.new_sha = patch['new_sha']
        # oids # an oid encoded in hex (40 bytes) # invalid oid = '0000...'
        self.old_file_sha = patch['old_oid']
        self.new_file_sha = patch['new_oid']
        self.status = patch['status']
        self.old_file_path = patch['old_file_path']
        self.new_file_path = patch['new_file_path']
        # TODO: remove self.filepath
        self.filepath = self.old_file_path
        self.additions = patch['additions']
        self.deletions = patch['deletions']
        self.similarity = patch['similarity']
        self.binary = patch['binary']
        self._generated = None

        # TODO: move to def init_comment_groups
        def func_filter(l):
            if l.has_oids:
                return l.from_oid == self.old_file_sha and l.to_oid == self.new_file_sha
            else:
                return l.from_sha == self.new_sha
        self.linecomments = filter(func_filter, linecomments)
        self.linecomments_has_linenum = []
        self.linecomments_has_pos = []
        for l in self.linecomments:
            (self.linecomments_has_pos,
             self.linecomments_has_linenum)[l.has_linenum].append(l)

        if is_limit_lines and self.additions + self.deletions > MAX_PATCH_MOD_LINES:
            self.is_toobig = True
            self.hunks = []
        else:
            self.is_toobig = False
            self.init_comment_groups()
            self.init_hunks(patch)

    def init_comment_groups(self):
        # TODO: 用 oids 做 linecomments 的过滤
        keyfunc_pos = lambda x: x.position
        keyfunc_line = lambda x: x.linenum
        self.comments_by_pos = {}
        self.comments_by_line = {}
        if self.linecomments_has_pos:
            self.linecomments_has_pos.sort(key=keyfunc_pos)
            self.comments_by_pos = dict((k, list(v))
                                        for k, v in groupby(self.linecomments_has_pos,
                                                            key=keyfunc_pos))
        if self.linecomments_has_linenum:
            self.linecomments_has_linenum.sort(key=keyfunc_line)
            self.comments_by_line = dict((k, list(v))
                                         for k, v in groupby(self.linecomments_has_linenum,
                                                             key=keyfunc_line))

    # TODO: refactor this!  T^T
    def init_hunks(self, raw_patch):
        ''' init Hunks, add extra_contexts when there're linecomments not involved '''
        EXTRE_CONTEXT_LINES = 3

        def expand_hunk(hunk, last_hunk_old_end, type,
                        MAX_LINE_NUM=99999,
                        MIN_LINE_NUM=0):
            if type == 'up':
                min_old_not_involved = MAX_LINE_NUM
                for linecomment in self.linecomments_has_linenum:
                    not_involved = False
                    old, new = linecomment.linenum
                    if old != LINECOMMENT_INDEX_EMPTY and new != LINECOMMENT_INDEX_EMPTY:
                        not_involved = last_hunk_old_end < old and old < hunk.old_start
                    if not_involved:
                        min_old_not_involved = min(min_old_not_involved, old)
                if min_old_not_involved != MAX_LINE_NUM:
                    contexts = self.get_contexts(min_old_not_involved - EXTRE_CONTEXT_LINES,
                                                 hunk.old_start)
                    if contexts:
                        hunk.expand_top_contexts(contexts)
            elif type == 'bottom':
                max_old_not_involved = MIN_LINE_NUM
                for linecomment in self.linecomments_has_linenum:
                    not_involved = False
                    old, new = linecomment.linenum
                    if old != LINECOMMENT_INDEX_EMPTY and new != LINECOMMENT_INDEX_EMPTY:
                        not_involved = last_hunk_old_end < old
                    if not_involved:
                        max_old_not_involved = max(max_old_not_involved, old)
                if max_old_not_involved != MIN_LINE_NUM:
                    contexts = self.get_contexts(hunk.old_end + 1,
                                                 max_old_not_involved + 1 + EXTRE_CONTEXT_LINES)
                    if contexts:
                        hunk.expand_bottom_contexts(contexts)

        self.hunks = [Hunk(self, h) for h in raw_patch['hunks']]
        if not self.hunks:
            return
        # TODO: 再 细分 pull/new pull/discussion compare 等？
        if self.linecomments_has_linenum and self.repo.provide('project'):
            last_hunk_old_end = 0
            for hunk in self.hunks:
                expand_hunk(hunk, last_hunk_old_end, type='up')
                last_hunk_old_end = hunk.old_end
            expand_hunk(hunk, last_hunk_old_end, type='bottom')
        if self.repo.provide('project'):
            first_hunk = self.hunks[0]
            last_hunk = self.hunks[-1]
            # add top_hunk
            if first_hunk.old_start > EXTRE_CONTEXT_LINES + 1:
                contexts = self.get_contexts(1, EXTRE_CONTEXT_LINES + 1)
                if contexts:
                    top_hunk = Hunk(self,
                                    old_start=1,
                                    new_start=1,
                                    old_lines=EXTRE_CONTEXT_LINES,
                                    new_lines=EXTRE_CONTEXT_LINES,
                                    contexts=contexts)
                    self.hunks.insert(0, top_hunk)
            elif first_hunk.old_start > 1:
                contexts = self.get_contexts(1, first_hunk.old_start)
                if contexts:
                    first_hunk.expand_top_contexts(contexts)
            # add bottom_hunk
            if last_hunk.old_end + EXTRE_CONTEXT_LINES < self.old_file_length:
                bottom_hunk_old_start = self.old_file_length - EXTRE_CONTEXT_LINES + 1
                bottom_hunk_new_start = self.new_file_length - EXTRE_CONTEXT_LINES + 1
                contexts = self.get_contexts(bottom_hunk_old_start,
                                             self.old_file_length + 1)
                if contexts:
                    bottom_hunk = Hunk(self,
                                       old_start=bottom_hunk_old_start,
                                       new_start=bottom_hunk_new_start,
                                       old_lines=EXTRE_CONTEXT_LINES,
                                       new_lines=EXTRE_CONTEXT_LINES,
                                       contexts=contexts)
                    self.hunks.append(bottom_hunk)
            elif last_hunk.old_end < self.old_file_length:
                contexts = self.get_contexts(last_hunk.old_end + 1,
                                             self.old_file_length + 1)
                if contexts:
                    last_hunk.expand_bottom_contexts(contexts)
        # update hunks
        pos = 1
        for i, hunk in enumerate(self.hunks):
            hunk.start_pos = pos
            pos += hunk.n_lines + 1  # +1 means hunk_heading
            if i > 0:
                last = self.hunks[i - 1]
                hunk.skipped_old_start = last.old_end + 1
                hunk.skipped_new_start = last.new_end + 1
                hunk.skipped_old_end = hunk.old_start - 1
                hunk.skipped_new_end = hunk.new_start - 1

    def get_contexts(self, start, end):
        ''' get patch's context lines in [start, end) '''
        if self.old_file_sha == INVALID_OID:
            ref = self.new_sha
        elif self.new_file_sha == INVALID_OID:
            ref = self.old_sha
        else:
            ref = self.old_sha or self.new_sha
        contexts = self.repo.get_contexts(ref, self.old_file_path,
                                          start, end)
        return contexts

    @property
    def old_file_length(self):
        if self._old_file_length is not None:
            return self._old_file_length

        if self.old_file_sha == INVALID_OID:
            self._old_file_length = 0
            return self._old_file_length

        ref = self.old_sha or self.new_sha
        self._old_file_length = self.repo.get_file_n_lines(ref, self.old_file_path)
        return self._old_file_length

    @property
    def new_file_length(self):
        if self._new_file_length is not None:
            return self._new_file_length

        if self.new_file_sha == INVALID_OID:
            self._new_file_length = 0
            return self._new_file_length

        ref = self.new_sha
        self._new_file_length = self.repo.get_file_n_lines(ref, self.new_file_path)
        return self._new_file_length

    @property
    def image(self):
        return is_image(self.old_file_path)

    @property
    def generated(self):
        # FIXME: generated 性能问题
        if self._generated is not None:
            return self._generated

        def get_data():
            data = ''
            try:
                if self.status == 'D':
                    blob = self.repo.get_file(self.old_sha, self.old_file_path)
                else:
                    blob = self.repo.get_file(self.new_sha, self.new_file_path)
                if blob:
                    data = blob.data
            except:  # very first commit ??
                data = ''
            return data

        generated = Generated.is_generated(self.new_file_path, get_data)
        self._generated = generated
        return generated

    #@property
    #def n_lines(self):
    #    return sum([hunk.n_lines for hunk in self.hunks])

    # TODO: remove this
    @property
    def content(self):
        content = []
        for h in self.hunks:
            content.append(h.heading)
            for l in h.lines:
                content.append(l)
        return content

    # TODO: rewrite
    # FIXME: more explanation
    def smart_slice(self, num):
        content = self.content[:num + 1]
        if len(content) > 15:
            tip_pos = 0
            for idx, line in enumerate(content):
                if line.old is None and line.new is None:
                    tip_pos = idx
            content = content[tip_pos:]
            if len(content) > 25:
                return content[-25:]
            else:
                return content
        return content
