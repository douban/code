# -*- coding: utf-8 -*-
from datetime import datetime

from ellen.utils import JagareError
from celery.schedules import crontab
from celery.task import periodic_task

from vilya.libs.store import store
from vilya.models.project import CodeDoubanProject
from vilya.models.doc import DocBuilder
from vilya.models.sphinx_docs import SphinxDocs
from vilya.models.elastic.issue_pr_search import IssuePRSearch
from vilya.models.elastic.indexer import IndexEngine
from vilya.models.user import get_users, clean_user_pulls
from vilya.models.team import Team
from vilya.models.ticket import TicketRank
from vilya.libs.gyt import is_git_dir
from vilya.libs.mq import async


# TODO: use sentry to catch exception
# TODO: move data accessors (mc keys) to model


def get_teams():
    rs = store.execute('select id from team')
    for id, in rs:
        yield Team.get(id)


def get_projects():
    rs = store.execute('select project_id from codedouban_projects')
    for proj_id, in rs:
        yield CodeDoubanProject.get(proj_id)


def get_origin_projects():
    rs = store.execute(
        'select project_id from codedouban_projects where project_id=origin_project')  # noqa
    for proj_id, in rs:
        yield CodeDoubanProject.get(proj_id)


def get_mirror_projects():
    rs = store.execute(
        'select project_id from codedouban_projects where owner_id=mirror')
    for proj_id, in rs:
        yield CodeDoubanProject.get(proj_id)


@async
def sphinx_builds_add(docs):
    docs.build_all()


@periodic_task(run_every=crontab(minute=0, hour=0))
def update_user_contributions():
    from vilya.models.contributions import UserContributions
    users = get_users()
    for user in users:
        UserContributions.update_by_user(user.name)


@periodic_task(run_every=crontab(minute=0, hour=6, day_of_week='sat'))
def project_fsck_and_gc():
    weekday = datetime.today().weekday()
    if weekday != 6:
        return
    result = get_projects()
    for proj in result:
        if is_git_dir(proj.git_dir) and not proj.git.is_empty():
            proj.git.call('fsck --full')
            proj.git.call('gc')
            proj.git.call('repack -adf')


@periodic_task(run_every=crontab(minute='*/30'))
def check_doc_builds():
    for proj in get_origin_projects():
        doc = DocBuilder(proj)
        if doc.can_build:
            sphinx_builds_add(doc)


@periodic_task(run_every=crontab(minute='*/30'))
def check_sphinx_builds():
    for proj in get_origin_projects():
        try:
            docs = SphinxDocs(proj.name)
        except JagareError:
            continue
        if not docs.enabled or not docs.need_rebuild():
            continue
        sphinx_builds_add(docs)


@periodic_task(run_every=crontab(minute=0, hour=6))
def update_elastic_index():
    results = get_projects()
    IndexEngine.delete_mapping('pull')
    IndexEngine.delete_mapping('issue')
    for proj in results:
        try:
            IssuePRSearch.index_a_project(proj)
        except:
            pass


@periodic_task(run_every=crontab(minute=0, hour=1))
def fetch_mirror_project():
    results = get_mirror_projects()
    for project in results:
        project.fetch()


@periodic_task(run_every=crontab(minute='*/15'))
def fetch_mirror_project_per_15m():
    results = get_mirror_projects()
    for project in results:
        mirror = project.mirror
        if mirror and mirror.frequency == 15:
            project.fetch()


@periodic_task(run_every=crontab(minute=15))
def update_user_pulls():
    users = get_users()
    for user in users:
        clean_user_pulls(user)


@periodic_task(run_every=crontab(minute=0, hour=12, day_of_week='sun'))
def send_team_week_report():
    from dispatches import dispatch
    for team in get_teams():
        if team.weekly:
            dispatch("weekly", data=dict(team_id=team.id))


@periodic_task(run_every=crontab(minute=0, hour='*'))
def update_ticket_rankscore_null():
    TicketRank.count_ticket_rank(False)


@periodic_task(run_every=crontab(minute=0, hour=0))
def update_ticket_rankscore_closed():
    TicketRank.count_ticket_rank(True)


def index_srcs_action():
    pass


def index_repos_action():
    pass


def index_users_action():
    pass


def index_a_project_docs():
    pass


def index_a_gist():
    pass
