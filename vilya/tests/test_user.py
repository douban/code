from framework import *
from unittest import TestCase
from vilya.models.user import User


class TestUser(TestCase):

    def setUp(self):
        super(TestUser, self).setUp()

    def tearDown(self):
        super(TestUser, self).tearDown()
        store.execute('truncate table users')
        store.commit()

    def test_create(self):
        password = "ilovecode"
        name = "code"
        desc = "description"
        email = "code@douco.de"
        user = User.create(name=name,
                           password=password,
                           description=desc,
                           email=email)
        self.assertEqual(user.name, name)
        self.assertEqual(user.email, email)
        self.assertEqual(user.description, desc)
        self.assertTrue(user.validate_password(password))
        self.assertEqual(len(user.projects), 0)
        self.assertIsNone(user.org)
