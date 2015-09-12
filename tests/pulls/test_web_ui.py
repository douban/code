# encoding: UTF-8

import os

from vilya.models.project import CodeDoubanProject
from vilya.models.pull import PullRequest

from tests.base import TestApp
from mock import patch
import tests
from tests.base import TestCase
from tests.utils import clone, mock_method

data_path = os.path.join(os.path.dirname(tests.__file__), 'data')


class TestWebUI(TestCase):
    def create_project_and_a_fork(self):
        from nose import SkipTest
        raise SkipTest(
            "These tests have Segmentation Fault")  # guibog 20121105
        orig = CodeDoubanProject.add('orig', 'origuser')
        with clone(orig.git_real_path) as workdir:
            with open(os.path.join(workdir, 'a'), 'w') as f:
                f.write("a line of code\n")

        fork = orig.fork('fork', 'forkuser')
        with clone(fork.git_real_path) as workdir:
            with open(os.path.join(workdir, 'b'), 'w') as f:
                f.write("another line of code\n")

        return orig, fork

    def create_an_auto_mergable_pull_request(self, from_proj):
        app = TestApp(extra_environ={'REMOTE_USER': str(from_proj.owner_id)})
        res = app.get('/%s' % str(from_proj.name))
        res = res.click("Pull Request")
        form = res.forms[1]
        form['body'] = "test"
        res = form.submit()
        while 300 < res.status_int < 400:
            res = res.follow()
        return res

    def test_new_pull_request_ticket_should_be_created_in_target_project(self):
        orig, fork = self.create_project_and_a_fork()
        res = self.create_an_auto_mergable_pull_request(fork)
        assert res.request.path == '/orig/pull/1'

    @patch.object(PullRequest, 'is_auto_mergable',
                  mock_method(PullRequest.is_auto_mergable))
    def test_check_auto_mergable_should_be_async_to_speed_up_page_response(self):  # noqa
        orig, fork = self.create_project_and_a_fork()
        res = self.create_an_auto_mergable_pull_request(fork)
        pull_url = res.request.path
        app = TestApp(extra_environ={'REMOTE_USER': str(orig.owner_id)})
        res = app.get(pull_url)
        assert not PullRequest.is_auto_mergable.mock.called
