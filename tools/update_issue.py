# -*- coding: utf-8 -*-


from vilya.libs.store import store


def main():
    rs = store.execute("select id, type "
                       "from issues "
                       "where type='project'")
    for r in rs:
        id, _ = r
        rs1 = store.execute("select id, project_id, issue_id "
                            "from project_issues "
                            "where issue_id=%s",
                            id)
        if rs1 and rs1[0]:
            _, target_id, _ = rs1[0]
            store.execute("update issues "
                          "set target_id=%s "
                          "where id=%s",
                          (target_id, id))
            store.commit()

    rs = store.execute("select id, type "
                       "from issues "
                       "where type='team'")
    for r in rs:
        id, _ = r
        rs1 = store.execute("select id, team_id, issue_id "
                            "from team_issues "
                            "where issue_id=%s",
                            id)
        if rs1 and rs1[0]:
            _, target_id, _ = rs1[0]
            store.execute("update issues "
                          "set target_id=%s "
                          "where id=%s",
                          (target_id, id))
            store.commit()


if __name__ == "__main__":
    main()
