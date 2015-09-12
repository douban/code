# -*- coding: utf-8 -*-
import time
import pickle
import zlib
import os
import datetime
from collections import defaultdict

from .consts import conf
from vilya.libs.store import get_db
from vilya.libs.permdir import get_repo_root

beansdb = get_db()


class DataCollector(object):
    """Manages data collection from a revision control repository."""
    def __init__(self):
        self.stamp_created = time.time()
        self.cache = {}
        self.total_authors = 0
        self.last_sha = ''
        self.h_of_day_act = defaultdict(int)  # hour -> commits
        self.d_of_week_act = defaultdict(int)  # day -> commits
        self.m_of_year_act = defaultdict(int)  # month [1-12] -> commits
        self.h_of_week_act = {}  # weekday -> hour -> commits
        self.h_of_day_act_busiest = 0
        self.h_of_week_act_busiest = 0
        self.year_week_act = defaultdict(int)  # yy_wNN -> commits
        self.year_week_act_peak = 0

        self.authors = {}
        # name -> {commits, first_commit_stamp, last_commit_stamp,
        #          last_active_day, active_days, lines_added,
        #          lines_removed}

        self.total_commits = 0
        self.total_files = 0
        self.authors_by_commits = 0

        # domains
        self.domains = {}  # domain -> commits

        # author of the month
        self.author_of_month = {}  # month -> author -> commits
        self.author_of_year = {}  # year -> author -> commits
        self.commits_by_month = defaultdict(int)  # month -> commits
        self.commits_by_year = defaultdict(int)  # year -> commits
        self.lines_added_by_month = defaultdict(int)  # month -> lines added
        self.lines_added_by_year = defaultdict(int)  # year -> lines added
        self.lines_removed_by_month = defaultdict(
            int)  # month -> lines removed
        self.lines_removed_by_year = defaultdict(int)  # year -> lines removed
        self.first_commit_stamp = 0
        self.last_commit_stamp = 0
        self.last_active_day = None
        self.active_days = set()

        # lines
        self.total_lines = 0
        self.total_lines_added = 0
        self.total_lines_removed = 0

        # size
        self.total_size = 0

        # timezone
        self.commits_by_timezone = defaultdict(int)  # timezone -> commits

        # tags
        self.tags = {}

        self.files_by_stamp = {}  # stamp -> files

        # extensions
        self.extensions = {}  # extension -> files, lines

        # line statistics
        self.changes_by_date = {}  # stamp -> { files, ins, del }

        self.changes_by_date_by_author = {}

    ##
    # This should be the main function to extract data from the repository.
    def collect(self, dir):
        self.dir = dir
        if len(conf['project_name']) == 0:
            self.projectname = os.path.basename(os.path.abspath(dir))
        else:
            self.projectname = conf['project_name']

    ##
    # Load cacheable data
    def loadCache(self, proj_name, key, n_author):
        try:
            data = beansdb.get(key, None)
            if data:
                self.cache = pickle.loads(zlib.decompress(data))
                if len(self.cache.get('authors')) != n_author:
                    self.cache = {}
        except Exception:
            self.cache = {}
        if not self.cache:
            path = os.path.join(get_repo_root(), 'statscache')
            try:
                f = open(os.path.join(path, '%s.cache' % proj_name), 'rb')
                self.cache = pickle.loads(zlib.decompress(f.read()))
                f.close()
            except Exception:
                self.cache = {}
        if self.cache:
            self.changes_by_date_by_author = self.cache.get(
                'changes_by_date_by_author', {})
            self.changes_by_date = self.cache.get('changes_by_date', {})
            self.authors = self.cache.get('authors', {})
            self.total_commits = self.cache.get('total_commits', 0)
            self.year_week_act = self.cache.get('year_week', defaultdict(int))
            self.year_week_act_peak = self.cache.get('year_week_peak', 0)
            self.total_lines = self.cache.get('total_lines', 0)
            self.total_lines_added = self.cache.get('total_lines_added', 0)
            self.total_lines_removed = self.cache.get('total_lines_removed', 0)

    ##
    # Produce any additional statistics from the extracted data.

    def refine(self):
        pass

    ##
    # : get a dictionary of author
    def getAuthorInfo(self, author):
        return None

    def getActivityByDayOfWeek(self):
        return {}

    def getActivityByHourOfDay(self):
        return {}

    # : get a dictionary of domains
    def getDomainInfo(self, domain):
        return None

    ##
    # Get a list of authors
    def getAuthors(self):
        return []

    def getFirstCommitDate(self):
        return datetime.datetime.now()

    def getLastCommitDate(self):
        return datetime.datetime.now()

    def getStampCreated(self):
        return self.stamp_created

    def getTags(self):
        return []

    def getTotalAuthors(self):
        return -1

    def getTotalCommits(self):
        return -1

    def getTotalFiles(self):
        return -1

    def getTotalLOC(self):
        return -1

    ##
    # Save cacheable data
    def saveCache(self, proj_name, key):
        proj_name = proj_name.replace('/', '_')
        self.cache['authors'] = self.authors
        self.cache['changes_by_date_by_author'] = self.changes_by_date_by_author  # noqa
        self.cache['total_commits'] = self.total_commits
        self.cache['changes_by_date'] = self.changes_by_date
        self.cache['year_week'] = self.year_week_act
        self.cache['year_week_peak'] = self.year_week_act_peak
        self.cache['total_lines'] = self.total_lines
        self.cache['total_lines_added'] = self.total_lines_added
        self.cache['total_lines_removed'] = self.total_lines_removed
        data = zlib.compress(pickle.dumps(self.cache))
        path = os.path.join(get_repo_root(), 'statscache/')
        if not os.path.exists(path):
            os.makedirs(path)
        tmp_name = os.path.join(path + '%s.cache.tmp' % proj_name)
        oldname = os.path.join(path + '%s.cache' % proj_name)
        try:
            os.remove(oldname)
        except OSError:
            pass
        f = open(tmp_name, 'wb')
        f.write(data)
        f.close()
        os.rename(tmp_name, oldname)
        try:
            beansdb.set(key, data)
        except Exception:
            pass
