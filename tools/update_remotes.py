#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from vilya.libs.store import store
from vilya.models.project import CodeDoubanProject

regex = re.compile(r"^/var/dae/apps/code/permdir/", re.IGNORECASE)


def get_projects():
    rs = store.execute('select project_id from codedouban_projects')
    for proj_id, in rs:
        yield CodeDoubanProject.get(proj_id)


for project in get_projects():
    remotes = project.repo.remotes
    for remote in remotes:
        url = remote.url
        if url.startswith('/var/dae/apps/code/permdir/'):
            new_url = regex.sub("/data/permdir/", url)
            remote.url = new_url
            remote.save()
            print project.name, remote.name, url
            print project.name, remote.name, new_url
