# -*- coding: utf-8 -*-

from isoweek import Week
from datetime import datetime, time as dtime
import time


def get_current_monday(timestamp=False):
    monday = datetime.combine(Week.thisweek().monday(), dtime.min)
    if timestamp:
        return time.mktime(monday.timetuple())
    return monday


def get_current_sunday(timestamp=False):
    sunday = datetime.combine(Week.thisweek().sunday(), dtime.min)
    if timestamp:
        return time.mktime(sunday.timetuple())
    return sunday


def get_last_monday(timestamp=False):
    monday = datetime.combine((Week.thisweek() - 1).monday(), dtime.min)
    if timestamp:
        return time.mktime(monday.timetuple())
    return monday


def get_last_sunday(timestamp=False):
    sunday = datetime.combine((Week.thisweek() - 1).sunday(), dtime.min)
    if timestamp:
        return time.mktime(sunday.timetuple())
    return sunday
