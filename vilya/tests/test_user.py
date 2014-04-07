from framework import *
from vilya.models.user import User


class TestUser(VilyaTestCase):

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
