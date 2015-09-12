# -*- coding: utf-8 -*-

from vilya.models.project_issue import ProjectIssue
from vilya.models.team_issue import TeamIssue
from vilya.libs.store import store


def main():
    rs = store.execute("select id, project_id, issue_id, number from project_issues")
    if rs:
        for r in rs:
            pi = ProjectIssue(*r)
            pi.update_rank_score()
    rs = store.execute("select id, team_id, issue_id, number from team_issues")
    if rs:
        for r in rs:
            ti = TeamIssue(*r)
            ti.update_rank_score()

if __name__ == '__main__':
    main()
