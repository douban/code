# -*- coding: utf-8 -*-

from vilya.libs.store import store

from vilya.models.project import CodeDoubanProject
from vilya.models.elastic.issue_pr_search import IssuePRSearch


def get_projects():
    rs = store.execute('select project_id from codedouban_projects')
    ids = (proj_id for proj_id, in rs)
    return CodeDoubanProject.gets(ids)


def main():
    projects = get_projects()
    for proj in projects:
        IssuePRSearch.index_a_project(proj)

if __name__ == "main":
    main()
