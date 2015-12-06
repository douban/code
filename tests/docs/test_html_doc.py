# -*- coding: utf-8 -*-

import os
from vilya.models.doc import HTMLDoc, DocBuilder
from tests.utils import get_temp_project
from tests.base import TestCase

DOC_REPO_PATH = os.path.join(os.path.dirname(__file__),
                             '../data/doc_repo')


class TestHTMLDoc(TestCase):

    def setUp(self):
        super(TestCase, self).setUp()
        self.project = get_temp_project(repo_path=DOC_REPO_PATH)
        project = self.project
        self.builder = DocBuilder(project, 'html')

    def tearDown(self):
        self.project.delete()
        super(TestCase, self).tearDown()

    def test_exists(self):
        doc = HTMLDoc(self.project, 'html', 'codeep-001.html')
        self.assertFalse(doc.exists)

        doc = HTMLDoc(self.project, 'html', 'codeep-002.html')
        self.assertFalse(doc.exists)

        self.builder.build()
        doc = HTMLDoc(self.project, 'html', 'codeep-001.html')
        self.assertTrue(doc.exists)

        doc = HTMLDoc(self.project, 'html', 'codeep-002.html')
        self.assertFalse(doc.exists)

    def test_is_template(self):
        self.builder.build()
        doc = HTMLDoc(self.project, 'html', 'codeep-001.html')
        self.assertIsNone(doc.is_template)

    def test_content(self):
        pass

    def test_content_type(self):
        pass

    def test_path(self):
        pass

    def test_doc_path(self):
        pass

    def teest_doc_id(self):
        pass
