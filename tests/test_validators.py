# -*- coding: utf-8 -*-

from tests.base import TestCase

from vilya.libs.validators import (
    check_name, check_url, check_integer, check_email,
    check_git_url, check_user_id, check_project_name)


class TestValidators(TestCase):
    def test_check_name(self):
        assert check_name("Sean") == None
        assert check_name("Sean Lee") == None
        assert check_name("Sean" * 50) == "Name is too long"

    def test_check_project_name(self):
        assert check_project_name("code") == None
        assert check_project_name("hubothubot") == None
        assert check_project_name("bot" * 50) != None
        assert check_project_name("c ode") != None
        assert check_project_name("我和你") != None
        assert check_project_name("asd/code") != None
        assert check_project_name("/////") != None

    def test_check_url(self):
        assert check_url("http://www.douban.com/people/ahbei") is None
        assert check_url("http://127.0.0.1:8000/") is None

        illegal_url = "wobushigeurl."
        very_long_url = "http://douban.com/%s" % "ahbei"* 500
        assert check_url(illegal_url) == "Url is illegal"
        assert check_url(very_long_url) == "Url is too long"

    def test_check_integer(self):
        assert check_integer("12312") == None
        assert check_integer("233.121") == "ID is not a integer"

    def test_check_email(self):
        assert check_email("test@douban.com") is None
        assert check_email("iseansay@gmail.com") is None
        assert check_email("@gmail.com") == "Email is non verified"

    def test_check_git_url(self):
        assert check_git_url(
            "http://code.dapps.douban.com/lisong_intern/code.git") is None
        assert check_git_url("https://github.com/liluo/py-oauth2.git") is None

    def test_check_user_id_(self):
        assert check_user_id("qingfeng") is not None
        assert check_user_id("verylonglonglonglonglongusername") is None
