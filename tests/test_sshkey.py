# -*- coding: utf-8 -*-

from tests.base import TestCase

from vilya.models.sshkey import SSHKey

KEY1 = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC9BDCAFpTC9h/0qEqYD62VRCYALKWBkJr"\
    "ll95hR8TDu3AOFLQCDZqEKcjzGrvoeEthwH++PTOv5mvYbwYmwtJb638tY/v7srxnFUCrrnzmZQqqY"\
    "T6ez+nOpJyDmBPPvQkNG9IRCoi14VnSWgsrSoYxCU9+mUldLmSt6N/kHbhTVq962kQOlnpoo0V+Cup"\
    "G1aE6UhuQs2Mug29GtCWMHfhtqv2ewYfUqPs+weFBYVHOj33H19HMeVmvJXWrAGawQiYs3RlLNvmdi"\
    "NOs2Jk7XeZakrkcvwjUbCLVXaNtVII/9Fnxn5dcA3kM43IU0W31RldJi8UI+mVgkjpvrrZHVaUN te"\
    "st@localhost"
KEY1_FINGERPRINT = "29:95:23:72:42:63:1f:97:8a:a7:01:a3:69:0d:0a:1b"
KEY1_TITLE = "test@localhost"

# incorrect
KEY2 = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC9BDCAFpTC9h/0qEqYD62VRCYALKWBkJr"\
    "T6tz+nOpJyDmBPPvQkNG9IRCoi14VnSWgsrSoYxCU9+mUldLmSt6N/kHbhTVq962kQOlnpoo0V+Cup"\
    "G1aE6UhuQs2Mug29GtCWMHfhtqv2ewYfUqPs+weFBYVHOj33H19HMeVmvJXWrAGawQiYs3RlLNvmdi"\
    "NOs2Jg7XeZakrkcvwjUbCLVXaNtVII/9Fnxn5dcA3kM43IU0W31RldJi8UI+mVgkjpvrrZHVaUN te"\
    "st@localhost"
# incorrect
KEY3 = "ssh-fsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC9BDCAFpTC9h/0qEqYD62VRCYALKWBkJr"\
    "ll95hR8TDu3AOFLQCDZqEKcjzGrvoeEthwH++PTOv5mvYbwYmwtJb638tY/v7srxnFUCrrnzmZQqqY"\
    "T6tz+nOpJyDmBPPvQkNG9IRCoi14VnSWgsrSoYxCU9+mUldLmSt6N/kHbhTVq962kQOlnpoo0V+Cup"\
    "G1aE6UhuQs2Mug29GtCWMHfhtqv2ewYfUqPs+weFBYVHOj33H19HMeVmvJXWrAGawQiYs3RlLNvmdi"\
    "NOs2Jk7XeZakrkcvwjUbCLVXaNtVII/9Fnxn5dcA3kM43IU0W31RldJi8UI+mVgkjpvrrZHVaUN te"\
    "st@localhost"
# correct
KEY4 = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC9BDCAFpTC9h/0qEqYD62VRCYALKWBkJr"\
    "ll95hR8TDu3AOFLQCDZqEKcjzGrvoeEthwH++PTOv5mvYbwYmwtJb638tY/v7srxnFUCrrnzmZQqqY"\
    "T6ez+nOpJyDmBPPvQkNG9IRCoi14VnSWgsrSoYxCU9+mUldLmSt6N/kHbhTVq962kQOlnpoo0V+Cup"\
    "G1aE6UhuQs2Mug29GtCWMHfhtqv2ewYfUqPs+weFBYVHOj33H19HMeVmvJXWrAGawQiYs3RlLNvmdi"\
    "NOs2Jk7XeZakrkcvwjUbCLVXaNtVII/9Fnxn5dcA3kM43IU0W31RldJi8UI+mVgkjpvrrZHVaUN"
# correct
KEY5 = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDOSD1H66ulGN23Sx/TeRClaEDYKEFt0V5Q"\
    "iQOl2nIISxjI2Z2GV+TGhtmqzrnY5tzCFXVUTblGs/+nuu8HSsrpJRgSHmafdm2ZhcG5fsVgJBT6mU6"\
    "v9dhn1Pb/L6yrcS1WiSxpq04v7x88LjyxKb38zoCn+EHA/IBQmUBixPT9kUJZEbzQmFbWnyP78HFHI0"\
    "QSGg+pkLlpqetcMHlLvJOzrTfGW8iARRSdf6CoH/iktWuCriv9OnDdKNQb1HImLRdtchz+iOD1B4gFH"\
    "gJ0XMBgqNRllpNHjn3DR8dFQDo00ooJT/lC0IR2ldt0vdZHPvvdiKHPZHm9QtY9LGa9p00F test5@l"\
    "ocalhost"


class TestSSHKey(TestCase):

    def test_add(self):
        key = SSHKey.add('test', KEY1)
        assert isinstance(key, SSHKey)
        assert key.fingerprint == KEY1_FINGERPRINT
        assert key.finger == KEY1_FINGERPRINT
        assert key.title == KEY1_TITLE
        assert key.key == KEY1

    def test_get(self):
        newkey = SSHKey.add('test', KEY1)
        key = SSHKey.get(newkey.id)
        assert isinstance(key, SSHKey)
        assert key.fingerprint == KEY1_FINGERPRINT
        assert key.finger == KEY1_FINGERPRINT
        assert key.title == KEY1_TITLE
        assert key.key == KEY1

    def test_delete(self):
        newkey = SSHKey.add('test', KEY1)
        newkey.delete()
        key = SSHKey.get(newkey.id)
        assert key is None

    def test_validate(self):
        r = SSHKey.validate('test', KEY1)
        assert r is True
        r = SSHKey.validate('test', KEY2)
        assert r is None
        r = SSHKey.validate('test', KEY3)
        assert r is None
        r = SSHKey.validate('test', KEY4)
        assert r is True

    def test_duplicate(self):
        SSHKey.add('test', KEY1)
        r = SSHKey.is_duplicated('test', KEY1)
        assert r is True
        r = SSHKey.is_duplicated('test', KEY5)
        assert r is None
