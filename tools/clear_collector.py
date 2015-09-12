#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from vilya.models.project import CodeDoubanProject
from vilya.models.stats.collector import DataCollector


def clear(project):
    data = DataCollector()
    data.saveCache(project, '/stats/' + project)


def clean_all():
    ids = CodeDoubanProject.get_ids()
    for id in ids:
        project = CodeDoubanProject.get(id)
        clear(project.name)


def reset_all():
    ids = CodeDoubanProject.get_ids()
    for id in ids:
        project = CodeDoubanProject.get(id)
        project.git.get_gitstats_data()


if __name__ == "__main__":
    argv = sys.argv
    if len(argv) == 2:
        project = argv[-1]
        if CodeDoubanProject.get_by_name(project):
            clear(project)
        else:
            print "Invalid project name."
