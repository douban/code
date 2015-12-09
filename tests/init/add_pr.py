# coding: utf-8
import os
import shutil
from os.path import join

from vilya.libs.permdir import get_repo_root
from vilya.libs.store import store
from vilya.models.project import CodeDoubanProject as Project
from vilya.models.pull import PullRequest
from vilya.models.ticket import Ticket

from tests.utils import clone

from local_config import DOMAIN

p1_name = "project1"
p1_id = None
p1_path = os.path.join(get_repo_root(), "%s.git" % p1_name)
shutil.rmtree(p1_path, ignore_errors=True)
p1 = Project.get_by_name(p1_name)
if p1:
    p1_id = p1.id
    p1.delete()

p2_name = "project2"
p2_id = None
p2_path = os.path.join(get_repo_root(), "%s.git" % p2_name)
shutil.rmtree(p2_path, ignore_errors=True)
p2 = Project.get_by_name(p2_name)
if p2:
    p2_id = p2.id
    p2.delete()

if p1_id:
    store.execute("delete from codedouban_ticket where project_id=%s", p1_id)
if p2_id:
    store.execute("delete from pullreq where from_project=%s", p2_id)
store.commit()


def setup2repos(proj1, proj2):
    path = proj1.git_real_path
    with clone(path) as workdir:
        with open(join(workdir, 'origin'), 'w') as f:
            f.write('origin')

    path = proj2.git_real_path
    with clone(path) as workdir:
        with open(join(workdir, 'origin'), 'w') as f:
            f.write('modified')

project = Project.add(
    p1_name, owner_id="testuser", summary="test", product="")
assert project
project_fork = Project.add(
    p2_name, owner_id="testuser", summary="test", product="",
    fork_from=project.id)

setup2repos(project, project_fork)

pullreq1 = PullRequest.open(project_fork, 'master', project, 'master')
ticket1 = Ticket.add(project.id, 'title', 'content', 'testuser')
pullreq1.insert(ticket1.ticket_number)

print "PR has been built at: %s" % (DOMAIN + ticket1.url)
