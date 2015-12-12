import unittest

from vilya.models.project import CodeDoubanProject
from vilya.models.hook import CodeDoubanHook
from tests.base import TestCase
from tests.utils import delete_project


class TestHook(TestCase):
    def setUp(self):
        TestCase.setUp(self)

    def _prj(self):
        delete_project('demo2')
        return CodeDoubanProject.add("demo2", owner_id="testuser1")

    def test_add_hook(self):
        url = "http://this.is.a.url"
        prj = self._prj()
        hook = CodeDoubanHook.add(url, prj.id)
        hooked_project = CodeDoubanProject.get(hook.project_id)
        assert hooked_project
        assert hook.__dict__ == hooked_project.hooks[0].__dict__

    def test_project_validate(self):
        wrong_url_hook = CodeDoubanHook(108, 'innotaurl', "100")
        wrong_project_id_hook = CodeDoubanHook(
            109, 'http://douaban.com', "noainteger")
        ok_hook = CodeDoubanHook(109, 'http://douaban.com', "101")
        assert wrong_url_hook.validate()
        assert wrong_project_id_hook.validate()
        assert not bool(ok_hook.validate())

    def test_destroy_hook(self):
        url = "http://this.is.other.url"
        prj = self._prj()
        hook = CodeDoubanHook.add(url, prj.id)
        hooked_project = CodeDoubanProject.get(hook.project_id)
        assert len(hooked_project.hooks) == 1
        hooked_project = CodeDoubanProject.get(hook.project_id)
        hook.destroy()
        assert len(hooked_project.hooks) == 0

if __name__ == '__main__':
    unittest.main()
