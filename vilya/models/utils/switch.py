# coding: utf-8

from vilya.libs.store import bdb


class WhiteListSwitch(object):

    DBKEY_SWITCH_PREFIX = "SWITCH_"

    def __init__(self, name):
        self.name = name

    @property
    def dbkey(self):
        return "%s%s" % (self.DBKEY_SWITCH_PREFIX, self.name)

    def get(self):
        return bdb.get(self.dbkey, [])

    def set(self, white_list):
        bdb.set(self.dbkey, white_list)
        return bdb.get(self.dbkey, [])

    def add(self, one):
        white_list = bdb.get(self.dbkey, [])
        if one not in white_list:
            white_list.append(one)
            bdb.set(self.dbkey, white_list)
            return bdb.get(self.dbkey, [])
        return white_list

    def remove(self, one):
        white_list = bdb.get(self.dbkey, [])
        if one in white_list:
            white_list.remove(one)
            bdb.set(self.dbkey, white_list)
            return bdb.get(self.dbkey, [])
        return white_list
