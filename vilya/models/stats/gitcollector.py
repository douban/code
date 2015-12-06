#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (c) 2007-2012 Heikki Hokkanen <hoxu@users.sf.net>
# & others (see doc/author.txt)
# GPLv2 / GPLv3
from datetime import datetime
from pytz import FixedOffset

from vilya.libs.consts import LANGUAGES
from vilya.libs.store import cache, ONE_DAY
from vilya.models.user import get_author_by_email
from .consts import conf
from .utils import getcommitrange, getkeyssortedbyvaluekey
from .collector import DataCollector

REPO_EXTENSION_KEY = "repo:%s:stats:extension1"


class GitDataCollector(DataCollector):

    def __init__(self, gyt_repo):
        super(GitDataCollector, self).__init__()
        self.gyt_repo = gyt_repo

    @classmethod
    def _get_author_email(cls, author_email):
        author, email = author_email.split('<', 1)
        author = author.rstrip()
        email = email.rstrip('>')
        return (author, email)

    def commitrange(self, head, end=None):
        return getcommitrange(head, end)

    def fill_shortstat(self, commitrange):
        try:
            to_ref, from_ref = commitrange
            block_of_lines = self.gyt_repo.repo.log(to_ref,
                                                    from_ref=from_ref,
                                                    shortstat=True,
                                                    no_merges=True,
                                                    reverse=True
                                                    )
        except:
            block_of_lines = []
        return block_of_lines

    @cache(REPO_EXTENSION_KEY % '{proj_name}', expire=ONE_DAY)
    def compute_file_size_and_extensions(self, proj_name):
        # extensions and size of files
        # this should only run once than only compute delta
        extensions = {}
        total_size = 0
        total_files = 0
        source_files = 0
        source_lines = 0
        lines = self.gyt_repo.repo.ls_tree('HEAD', recursive=True, size=True)
        for line in lines:
            if line[0] == '160000' and line[3] == '-':
                # skip submodules
                continue
            sha1 = line[2]
            size = int(line[3])
            fullpath = line[4]

            total_size += size
            total_files += 1

            filename = fullpath.split('/')[-1]  # strip directories
            if filename.find('.') == -1 or filename.rfind('.') == 0:
                ext = ''
            else:
                ext = filename[(filename.rfind('.') + 1):]
            if len(ext) > conf['max_ext_length']:
                ext = ''
            name = LANGUAGES.get(ext, None)

            if name not in extensions:
                if ext in LANGUAGES.keys():
                    name = LANGUAGES[ext]
                    extensions[name] = {'files': 0, 'lines': 0}
                else:
                    continue

            extensions[name]['files'] += 1
            source_files += 1
            try:
                # should be text files
                count = self.getLinesInBlob(sha1)
                extensions[name]['lines'] += count
                source_lines += count
            except:
                pass
        return extensions, total_files, total_size, source_files, source_lines

    def fill_rev_list_commitrange(self, commitrange):
        to_ref, from_ref = commitrange
        commits = self.gyt_repo.repo.rev_list(to_ref, from_ref)
        for commit in commits:
            author = commit.author.name
            # email = email_normalizer(commit.author.name,
            #                          commit.author.email)
            email = commit.author.email
            stamp = commit.committer.time
            date = datetime.fromtimestamp(
                commit.committer.time,
                FixedOffset(commit.committer.offset)
            )

            author = get_author_by_email(email, author)
            if author in conf['merge_authors']:
                author = conf['merge_authors'][author]

            # First and last commit stamp
            # (may be in any order because of cherry-picking and patches)
            if stamp > self.last_commit_stamp:
                self.last_commit_stamp = stamp
            if self.first_commit_stamp == 0 or stamp < self.first_commit_stamp:
                self.first_commit_stamp = stamp

            # yearly/weekly activity
            yyw = date.strftime('%Y-%W')
            self.year_week_act[yyw] += 1
            if self.year_week_act_peak < self.year_week_act[yyw]:
                self.year_week_act_peak = self.year_week_act[yyw]

            # author stats
            if author not in self.authors:
                self.authors[author] = {
                    'lines_added': 0,
                    'lines_removed': 0,
                    'commits': 0,
                }
            # commits, note again that commits may be in any date order
            # because of cherry-picking and patches
            if 'last_commit_stamp' not in self.authors[author]:
                self.authors[author]['last_commit_stamp'] = stamp
            if stamp > self.authors[author]['last_commit_stamp']:
                self.authors[author]['last_commit_stamp'] = stamp
            if 'first_commit_stamp' not in self.authors[author]:
                self.authors[author]['first_commit_stamp'] = stamp
            if stamp < self.authors[author]['first_commit_stamp']:
                self.authors[author]['first_commit_stamp'] = stamp
            if 'email' not in self.authors[author]:
                self.authors[author]['email'] = email

    def fill_short_stats_commitrange(self, commitrange):
        to_ref, from_ref = commitrange
        if to_ref == 'HEAD' and from_ref is None:
            total_lines = 0
        else:
            total_lines = self.total_lines
        for commit in self.fill_shortstat(commitrange):
            files = commit['files']
            inserted = commit['additions']
            deleted = commit['deletions']
            total_lines += inserted
            total_lines -= deleted
            self.total_lines_added += inserted
            self.total_lines_removed += deleted
            stamp = commit['committer_time']
            author = commit['author_name']
            email = commit['author_email']
            author = get_author_by_email(email, author)
            if author in conf['merge_authors']:
                author = conf['merge_authors'][author]
            self.changes_by_date[stamp] = {
                'files': files,
                'ins': inserted,
                'del': deleted,
                'lines': total_lines
            }
            self.process_line_user(author, stamp, inserted, deleted)
        self.total_lines = total_lines

    def collect(self, dir, proj_name, head, n_author):
        DataCollector.collect(self, dir)
        self.loadCache(proj_name, '/stats/' + proj_name, n_author)
        last_sha = self.cache and self.cache.get('last_sha', '')
        if last_sha:
            commitrange = self.commitrange('HEAD', last_sha)
        else:
            commitrange = self.commitrange('HEAD')

        self.total_authors += n_author
        self.fill_rev_list_commitrange(commitrange)

        # TODO Optimize this, it's the worst bottleneck
        # outputs "<stamp> <files>" for each revision
        to_ref, from_ref = commitrange
        revlines = self.gyt_repo.repo.rev_list(to_ref, from_ref=from_ref)
        for commit in revlines:
            timest = commit.author.time
            rev = commit.tree.hex
            linecount = self.getFilesInCommit(rev)
            self.files_by_stamp[int(timest)] = int(linecount)
        self.total_commits += len(revlines)

        extensions, total_files, total_size, source_files, source_lines \
            = self.compute_file_size_and_extensions(proj_name)

        self.extensions = extensions
        self.total_files = total_files
        self.total_size = total_size
        self.source_files = source_files
        self.source_lines = source_lines

        self.fill_short_stats_commitrange(commitrange)

        self.refine()
        # here update new data after head sha

        # here need to save to cache up to head sha
        self.cache['last_sha'] = head
        self.saveCache(proj_name, '/stats/' + proj_name)

    def process_line_user(self, author, stamp, inserted, deleted):
        if author not in self.authors:
            self.authors[author] = {
                'lines_added': 0,
                'lines_removed': 0,
                'commits': 0,
            }
        self.authors[author]['commits'] += 1
        self.authors[author]['lines_added'] += inserted
        self.authors[author]['lines_removed'] += deleted
        if stamp not in self.changes_by_date_by_author:
            self.changes_by_date_by_author[stamp] = {}
        if author not in self.changes_by_date_by_author[stamp]:
            self.changes_by_date_by_author[stamp][author] = {}
        linesadd = self.authors[author]['lines_added']
        commits_n = self.authors[author]['commits']
        self.changes_by_date_by_author[stamp][author]['lines_added'] = linesadd
        self.changes_by_date_by_author[stamp][author]['commits'] = commits_n

    def refine(self):
        # authors
        # name -> {place_by_commits, commits_frac, date_first, date_last,
        # timedelta}
        self.authors_by_commits = getkeyssortedbyvaluekey(
            self.authors, 'commits')
        self.authors_by_commits.reverse()  # most first
        for i, name in enumerate(self.authors_by_commits):
            self.authors[name]['place_by_commits'] = i + 1

        for name in self.authors.keys():
            a = self.authors[name]
            a['commits_frac'] = (
                100 * float(a['commits'])) / self.getTotalCommits()
            date_first = datetime.fromtimestamp(a['first_commit_stamp'])
            date_last = datetime.fromtimestamp(a['last_commit_stamp'])
            delta = date_last - date_first
            a['date_first'] = date_first.strftime('%Y-%m-%d')
            a['date_last'] = date_last.strftime('%Y-%m-%d')
            a['timedelta'] = delta
            if 'lines_added' not in a:
                a['lines_added'] = 0
            if 'lines_removed' not in a:
                a['lines_removed'] = 0

    def getActiveDays(self):
        return self.active_days

    def getActivityByDayOfWeek(self):
        return self.d_of_week_act

    def getActivityByHourOfDay(self):
        return self.h_of_day_act

    def getAuthorInfo(self, author):
        return self.authors[author]

    def getAuthors(self, limit=None):
        res = getkeyssortedbyvaluekey(self.authors, 'commits')
        res.reverse()
        return res[:limit]

    def getCommitDeltaDays(self):
        return (self.last_commit_stamp / 86400 - self.first_commit_stamp / 86400) + 1  # noqa

    def getFilesInCommit(self, rev):
        try:
            res = self.cache['files_in_tree'][rev]
        except:
            res = len(self.gyt_repo.repo.ls_tree(rev,
                                                 recursive=True,
                                                 name_only=True))
            if 'files_in_tree' not in self.cache:
                self.cache['files_in_tree'] = {}
            self.cache['files_in_tree'][rev] = res

        return res

    def getFirstCommitDate(self):
        return datetime.fromtimestamp(self.first_commit_stamp)

    def getLastCommitDate(self):
        return datetime.fromtimestamp(self.last_commit_stamp)

    def getLinesInBlob(self, sha1):
        try:
            res = self.cache['lines_in_blob'][sha1]
        except:
            res = len(self.gyt_repo.repo.cat_file(sha1).split('\n'))
            if 'lines_in_blob' not in self.cache:
                self.cache['lines_in_blob'] = {}
            self.cache['lines_in_blob'][sha1] = res
        return res

    def getTotalAuthors(self):
        return self.total_authors

    def getTotalCommits(self):
        return self.total_commits

    def getTotalFiles(self):
        return self.total_files

    def getTotalLOC(self):
        return self.total_lines

    def getTotalSize(self):
        return self.total_size
