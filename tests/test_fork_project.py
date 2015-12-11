import os
import shutil

from vilya.models.project import CodeDoubanProject
from nose.tools import ok_, eq_

from tests.base import TestCase


def rmtree(path):
    if os.path.exists(path):
        shutil.rmtree(path)


class TestProject(TestCase):

    def test_fork_project(self):
        orig = CodeDoubanProject.add('orig', owner_id="user1")
        fork = orig.fork('fork', 'user2')

        ok_(os.path.exists(fork.git_real_path))
        ok_(os.path.exists(os.path.join(fork.git_real_path, 'HEAD')))

        eq_(fork.owner_id, 'user2')

    def test_get_forked_from_should_return_origin_project(self):
        prj = CodeDoubanProject.get_by_name('orig')
        prj.delete()
        prj = CodeDoubanProject.get_by_name('fork')
        prj.delete()
        orig = CodeDoubanProject.add('orig', owner_id="test1")
        fork = orig.fork('fork', 'user2')
        source = fork.get_forked_from()
        eq_(source, orig)

    def test_get_fork_network_should_return_all_projects_with_same_origin(self):  # noqa
        prj = CodeDoubanProject.get_by_name('orig')
        prj.delete()
        orig = CodeDoubanProject.add('orig', owner_id="test1")
        fork = orig.fork('fork1', 'user1')
        fork2 = orig.fork('fork2', 'user2')
        fork3 = fork.fork('fork3', 'user3')

        expected_network = set([orig, fork, fork2, fork3])

        for proj in [orig, fork, fork2, fork3]:
            network = proj.get_fork_network()
            eq_(set(network), expected_network)
