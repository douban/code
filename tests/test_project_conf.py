from tests.base import TestCase

from vilya.models.project import CodeDoubanProject
from vilya.models.project_conf import PROJECT_CONF_FILE

from nose.tools import raises


class TestProjectConf(TestCase):

    def test_create_project_without_conf(self):
        self.clean_up()
        project = CodeDoubanProject.add(
            'tp', owner_id="test1", create_trac=False)
        assert project.conf['docs'], "enabled by default"

    def test_conf_add_wrong_keys(self):
        self.clean_up()
        project = CodeDoubanProject.add(
            'tp', owner_id="test1", create_trac=False)
        u = self.addUser()
        project.git.commit_one_file(
            PROJECT_CONF_FILE,
            'unexisting_key_argl1: 1\nunexisting_key_argl2: 2', 'm', u)
        assert 'unexisting_key_argl1' not in project.conf

    def test_conf(self):
        self.clean_up()
        project = CodeDoubanProject.add(
            'tp', owner_id="test1", create_trac=False)
        u = self.addUser()
        project.git.commit_one_file(PROJECT_CONF_FILE,
                                    'docs: {Docs: {dir: other_dir}}', 'm', u)
        assert project.conf['docs']['Docs']['dir'] == 'other_dir'

    @raises(Exception)
    def test_broken_conf(self):
        self.clean_up()
        project = CodeDoubanProject.add(
            'tp', owner_id="test1", create_trac=False)
        u = self.addUser()
        project.git.commit_one_file(PROJECT_CONF_FILE,
                                    'docs {dir: other_dir', 'm', u)
        assert project.conf['docs']['dir'] == 'other_dir'

    def test_cannot_set_undefined_first_level_entry(self):
        self.clean_up()
        project = CodeDoubanProject.add(
            'tp', owner_id="test1", create_trac=False)
        u = self.addUser()
        project.git.commit_one_file(PROJECT_CONF_FILE,
                                    'unexisting_key: 123', 'm', u)
        # First level key need to be defined in default_code_config.yaml
        assert 'unexisting_key' not in project.conf

    def test_can_set_undefined_second_level_entry(self):
        self.clean_up()
        project = CodeDoubanProject.add(
            'tp', owner_id="test1", create_trac=False)
        u = self.addUser()
        project.git.commit_one_file(PROJECT_CONF_FILE,
                                    'docs: {unexisting_key: aaa}', 'm', u)
        assert project.conf['docs']['unexisting_key'] == 'aaa'

    def clean_up(self):
        prj = CodeDoubanProject.get_by_name('tp')
        if prj:
            prj.delete()
