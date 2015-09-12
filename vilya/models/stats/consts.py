# -*- coding: utf-8 -*-
import platform

ON_LINUX = (platform.system() == 'Linux')
WEEKDAYS = ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')

conf = {
    'max_domains': 10,
    'max_ext_length': 10,
    'style': 'gitstats.css',
    'max_authors': 20,
    'authors_top': 5,
    'commit_begin': '',
    'commit_end': 'HEAD',
    'linear_linestats': 1,
    'project_name': '',
    'merge_authors': {}
}
