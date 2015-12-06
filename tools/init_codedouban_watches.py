# -*- coding: utf-8 -*-

import sys
import MySQLdb
from vilya.libs.store import store
from traceback import print_exc


def main():
    try:
        rs = store.execute("select project_id,owner_id from codedouban_projects")
        for r in rs:
            try:
                store.execute("insert into codedouban_watches (project_id, user_id) "
                              "values (%s, %s)",
                              (r[0], r[1]))
            except MySQLdb.IntegrityError, e:
                 print_exc()
        store.commit()
    except Exception, e:
        print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
