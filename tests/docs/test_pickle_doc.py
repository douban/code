# -*- coding: utf-8 -*-

import os
from vilya.models.doc import PickleDoc, DocBuilder
from tests.utils import get_temp_project
from tests.base import TestCase

DOC_REPO_PATH = os.path.join(os.path.dirname(__file__),
                             '../data/doc_repo')


class TestPickleDoc(TestCase):

    def setUp(self):
        super(TestCase, self).setUp()
        self.project = get_temp_project(repo_path=DOC_REPO_PATH)
        project = self.project
        self.builder = DocBuilder(project, 'pickle')

    def tearDown(self):
        self.project.delete()
        super(TestCase, self).tearDown()

    def test_exists(self):
        doc = PickleDoc(self.project, 'pickle', 'codeep-001')
        self.assertIsNone(doc.exists)

        doc = PickleDoc(self.project, 'pickle', 'codeep-002')
        self.assertIsNone(doc.exists)

        self.builder.build()
        doc = PickleDoc(self.project, 'pickle', 'codeep-001')
        self.assertTrue(doc.exists)

        doc = PickleDoc(self.project, 'pickle', 'codeep-002')
        self.assertIsNone(doc.exists)

    def test_is_template(self):
        self.builder.build()
        doc = PickleDoc(self.project, 'pickle', 'codeep-001')
        self.assertTrue(doc.is_template)
        doc = PickleDoc(self.project, 'pickle', '_sources/codeep-001.txt')
        self.assertFalse(doc.is_template)
        doc = PickleDoc(self.project, 'pickle', '_static/pygments.css')
        self.assertFalse(doc.is_template)

    def test_content(self):
        self.builder.build()
        doc = PickleDoc(self.project, 'pickle', 'codeep-001')
        self.assertTrue(isinstance(doc.content, dict))

    def test_content_type(self):
        pass

    def test_path(self):
        pass

    def test_doc_path(self):
        pass

    def teest_doc_id(self):
        pass
