# -*- coding: utf-8 -*-

from __future__ import absolute_import
from vilya.models.ngit.blob import Blob


class Blame(object):

    def __init__(self, repo, blame):
        self.repo = repo
        self._blame = blame
        self.blob = Blob(repo, blame['blob'])
        self.blob_lines = self.blob.data.splitlines()
        self.hunks = [BlameHunk(self, hunk)
                      for hunk in blame['hunks']]


class BlameHunk(object):

    def __init__(self, blame, hunk):
        self.blame = blame
        self.blob = blame.blob
        self.final_commit_id = hunk['final_commit_id']
        self.final_start_line_number = hunk['final_start_line_number']
        self.orig_path = hunk['orig_path']
        self.orig_commit_id = hunk['orig_commit_id']
        self.orig_start_line_number = hunk['orig_start_line_number']
        self.commit = blame.repo.get_commit(self.final_commit_id)
        self.orig_commit = blame.repo.get_commit(self.orig_commit_id)
        self.lines = [BlameLine(self, idx)
                      for idx in range(hunk['lines_in_hunk'])]


class BlameLine(object):

    def __init__(self, hunk, idx):
        self._hunk = hunk
        self.idx = idx
        self.no = hunk.final_start_line_number + idx
        self.orig_no = hunk.orig_start_line_number + idx
        self.content = hunk.blame.blob_lines[self.no - 1]
        self.commit = hunk.commit
        self.orig_commit = hunk.orig_commit
        self.orig_sha = (hunk.orig_commit.sha
                         if hunk.orig_commit else hunk.commit.sha)
        self.path = hunk.orig_path

    @property
    def url(self):
        return "%s%s#L-%s" % (self.commit.url,
                              self.hunk.orig_path,
                              self.line_no)

    @property
    def orig_path_url(self):
        # FIXME: urlencode path
        return "/%s/blob/%s/%s#L-%s" % (self._hunk.blame.repo.name,
                                        self.orig_sha,
                                        self.path,
                                        self.orig_no)
