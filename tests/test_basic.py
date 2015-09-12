import os
import shutil

from vilya.libs.permdir import get_repo_root
from vilya.models.project import CodeDoubanProject

from tests.base import TestCase


class TestBasic(TestCase):
    def test_create_git_repo(self):
        git_path = os.path.join(get_repo_root(), 'abc.git')
        CodeDoubanProject.create_git_repo(git_path)
        assert os.path.exists(git_path)
        info_file = os.path.join(git_path, 'refs')
        assert os.path.exists(info_file)
        shutil.rmtree(git_path)
