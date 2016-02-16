# -*- coding: utf-8 -*-

from __future__ import absolute_import
import os
from datetime import datetime

from nose.tools import ok_

from tests.base import TestCase

from vilya.config import DOMAIN
from vilya.models.project import CodeDoubanProject
from vilya.libs.gravatar import gravatar_url
from vilya.libs.permdir import get_repo_root


class TestProject(TestCase):

    def test_create_project(self):
        project_name = "project"
        project = CodeDoubanProject.add(
            project_name, owner_id="test1", summary="test", product="fire")

        git_path = os.path.join(get_repo_root(), '%s.git' % project_name)
        ok_(os.path.exists(git_path))
        project.delete()

    # 本地开发禁用hook了
    # def test_create_project_with_hook(self):
    #    project_name = "project2"
    #    project = CodeDoubanProject.add(
    #        project_name, owner_id="test1", summary="test", product="fire")
    #    hookfile_path = "%s/hooks/post-receive" % project.git_real_path
    #    ok_(os.path.exists(hookfile_path))
    #    project.delete()

    def test_project_meta_dict(self):
        project_name = "project3"
        owner_id = "testuser"
        summary = "a summary"
        product = "fire"
        project = CodeDoubanProject.add(
            project_name, owner_id, summary, product)
        # hookfile_path = "%s/hooks/post-receive" % project.git_real_path
        project = CodeDoubanProject.get_by_name(project_name)
        data = {
            'url': "%s/%s" % (DOMAIN, project_name),
            'name': project_name,
            'description': summary,
            'product': product,
            'committers_count': 0,
            'forked_count': 0,
            'open_issues_count': 0,
            'open_tickets_count': 0,
            'watched_count': 0,
            'owner': {
                'name': owner_id,
                'avatar': gravatar_url(owner_id + '@douban.com'),
            },
        }
        commits = project.git.get_revisions("HEAD~1", "HEAD")
        if commits:
            data['last_commit'] = commits[0]
        ok_(project.get_info() == data)
        project.delete()

    def test_project_validate(self):
        noname_project = CodeDoubanProject(
            108, '', "test1", "testuser", datetime.now(), "fire",
            '/fake_path', '/fake_path')
        ok_project = CodeDoubanProject(
            108, 'project6', "testuser", datetime.now(), "test",
            "fire", '/fake_path', '/fake_path')
        ok_(bool(noname_project.validate()))
        ok_(not bool(ok_project.validate()))

    def test_permissions_check(self):
        project_name = "project4"
        project = CodeDoubanProject.add(project_name, owner_id="admin_user",
                                        summary="test", product="fire")
        ok_(project.is_admin("admin_user"))
        ok_(not project.is_admin("other_user"))
        project.delete()

    def test_delete_project(self):
        project_name = "project5"
        project = CodeDoubanProject.add(project_name, owner_id="admin_user",
                                        summary="test", product="fire")

        git_path = os.path.join(get_repo_root(), '%s.git' % project_name)
        ok_(os.path.isdir(git_path))
        project.delete()
        ok_(not os.path.exists(git_path))

    def test_fork_and_watch_project(self):
        p6 = CodeDoubanProject.add('project6', owner_id="admin_user",
                                   summary="test", product="fire")
        p7 = CodeDoubanProject.add('project7', owner_id="other_user",
                                   summary="test", product="fire")

        fork_count = CodeDoubanProject.get_forked_count(p6.id)
        p6fork = p6.fork('project6_other_user', 'other_user')
        fork_count2 = CodeDoubanProject.get_forked_count(p6.id)
        ok_(fork_count2 == fork_count + 1)
        ok_(CodeDoubanProject.get_forked_count(p6fork.id) == 0)

        p6fork2 = p6fork.fork('project6_fork_other_user', 'other_user')
        ok_(CodeDoubanProject.get_forked_count(p6.id) == fork_count + 2)
        ok_(CodeDoubanProject.get_forked_count(p6fork.id) == 1)
        ok_(CodeDoubanProject.get_forked_count(p6fork2.id) == 0)

        watch_count = CodeDoubanProject.get_watched_count(p7.id)
        CodeDoubanProject.add_watch(p7.id, 'admin_user')
        watch_count2 = CodeDoubanProject.get_watched_count(p7.id)
        ok_(watch_count2 == watch_count + 1)

        ok_(len(p7.get_watch_users()) == watch_count2)

        p6.delete()
        p7.delete()

    def test_transfer_project(self):
        pname1 = 'project6'
        pname2 = 'project7'
        proj_owner = 'admin_user'
        to_user = 'testuser1'
        p = CodeDoubanProject.add(pname1, owner_id=proj_owner,
                                  summary="test", product="fire")
        _ = CodeDoubanProject.add(pname2, owner_id=proj_owner,
                                  summary="test", product="fire")
        p.transfer_to(to_user)
        p1 = CodeDoubanProject.get_by_name(pname1)
        assert p1.owner_id == to_user
        p2 = CodeDoubanProject.get_by_name(pname2)
        assert p2.owner_id == proj_owner

    def test_rename_project(self):
        pname1 = 'project8'
        pname2 = 'project9'
        proj_owner = 'admin_user'
        p = CodeDoubanProject.add(pname1, owner_id=proj_owner,
                                  summary="test", product="fire")
        p.rename(pname2)
        assert p.name == pname2
        git_path = os.path.join(get_repo_root(), '%s.git' % pname2)
        ok_(os.path.exists(git_path))

    def test_rename_bad_project(self):
        pname1 = 'project10'
        pname2 = '/dad13/'
        proj_owner = 'admin_user'
        p = CodeDoubanProject.add(pname1, owner_id=proj_owner,
                                  summary="test", product="fire")
        assert p.rename(pname2) is False
        git_path = os.path.join(get_repo_root(), '%s.git' % pname1)
        ok_(os.path.exists(git_path))

    def test_update_can_push(self):
        project_name = "project11"
        owner_id = "testuser"
        summary = "a summary"
        product = "fire"
        CodeDoubanProject.add(project_name,
                              owner_id,
                              summary,
                              product)
        p = CodeDoubanProject.get_by_name('project11')
        assert p.can_push == 1
        p.update_can_push(False)
        p = CodeDoubanProject.get_by_name('project11')
        assert p.can_push == 0
        p.update_can_push(True)
        p = CodeDoubanProject.get_by_name('project11')
        assert p.can_push == 1
