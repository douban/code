from framework import *
from unittest import TestCase
from vilya.models.project import Project


class TestProject(TestCase):
    def test_add(self):
    	proj_name = "test_project"
    	proj = Project.add(name=proj_name, owner_id=1, creator_id=1)
    	assert proj.name == proj_name