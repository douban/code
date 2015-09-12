# -*- coding: utf-8 -*-

from vilya.libs.store import store, bdb

BDB_ISSUE_DESCRIPTION_KEY = 'issue_description:%s'


def main():
    ds = []
    rs = store.execute("select id, project_id, issue_id "
                       "from project_issues")
    for r in rs:
        id = r[0]
        project_id = r[1]
        issue_id = r[2]
        description = bdb.get(BDB_ISSUE_DESCRIPTION_KEY % id)
        bdb.delete(BDB_ISSUE_DESCRIPTION_KEY % id)
        ds.append([issue_id, description])

    for d in ds:
        issue_id = d[0]
        description = d[1]
        bdb.set(BDB_ISSUE_DESCRIPTION_KEY % issue_id, description)


if __name__ == "__main__":
    main()
