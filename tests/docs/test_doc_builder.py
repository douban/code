# -*- coding: utf-8 -*-

import os
from vilya.models.doc import DocBuilder
from tests.utils import get_temp_project
from tests.base import TestCase

DOC_REPO_PATH = os.path.join(os.path.dirname(__file__),
                             '../data/doc_repo')


class TestDocBuilder(TestCase):

    def setUp(self):
        super(TestCase, self).setUp()
        self.project = get_temp_project(repo_path=DOC_REPO_PATH)

    def tearDown(self):
        self.project.delete()
        super(TestCase, self).tearDown()

    def test_can_build(self):
        project = self.project
        builder = DocBuilder(project, 'pickle')
        self.assertTrue(builder.can_build)

    def test_up_to_date(self):
        project = self.project
        builder = DocBuilder(project, 'pickle')
        self.assertFalse(builder.up_to_date)

    def test_in_queue(self):
        pass

    def test_enqueue(self):
        pass

    def test_dequeue(self):
        pass

    def test_build(self):
        project = self.project
        builder = DocBuilder(project, 'pickle')
        builder.build()
        test_path = builder.option.builder_doc_path
        self.assertTrue(os.path.exists("%s/codeep-001.fpickle" %
                                       test_path))
        self.assertTrue(os.path.exists("%s/index.fpickle" %
                                       test_path))
        self.assertTrue(os.path.exists("%s/genindex.fpickle" %
                                       test_path))
        self.assertTrue(os.path.exists("%s/search.fpickle" %
                                       test_path))
        self.assertTrue(os.path.exists("%s/environment.pickle" %
                                       test_path))

        builder = DocBuilder(project, 'html')
        builder.build()
        test_path = builder.option.builder_doc_path
        self.assertTrue(os.path.exists("%s/codeep-001.html" %
                                       test_path))
        self.assertTrue(os.path.exists("%s/genindex.html" %
                                       test_path))
        self.assertTrue(os.path.exists("%s/search.html" %
                                       test_path))
        self.assertTrue(os.path.exists("%s/index.html" %
                                       test_path))

        builder = DocBuilder(project, 'raw')
        builder.build()
        test_path = builder.option.builder_doc_path
        self.assertTrue(os.path.exists("%s/code-logo.png" %
                                       test_path))
        self.assertTrue(os.path.exists("%s/index.html" %
                                       test_path))
