# -*- coding: utf-8 -*-

import time

def compute_relative_time(timestamp=1340875790):
    #git/data.c void show_date_relative
    delta = int(time.time()) - int(timestamp)
    # In unitests we have 0 or 1 seconds, not stable, better say 'few' when below 10 s.
    if delta < 10:
        return "few seconds ago"
    if delta < 90:
        return str(delta) + " seconds ago"
    #Turn it into minutes
    delta = (delta + 30) / 60
    if delta < 90:
        return str(delta) + " minutes ago"
    #Turn it into hours
    delta = (delta + 30) / 60
    if delta < 36:
        return str(delta) + " hours ago"
    #We deal with number of days from here on
    delta = (delta + 12) / 24
    if delta < 14:
        return str(delta) + " days ago"
    #Say weeks for the past 10 weeks or so
    if delta < 70:
        return str((delta + 3) / 7) + " weeks ago"
    #Say months for the past 12 months or so
    if delta < 365:
        return str((delta + 15) / 30) + " months ago"
    #Give years and months for 5 years or so */
    if delta < 1825:
        totalmonths = (delta * 12 * 2 + 365) / (365 * 2)
        years = totalmonths / 12
        months = totalmonths % 12
        if years == 1:
            if months > 1:
                return "1 year, %s months ago" % months
            elif months == 1:
                return "1 year, 1 month ago"
            else:
                return "1 year ago"
        else:
            if months == 1:
                return "%s years, 1 month ago" % years
            elif months:
                return "%s years, %s months ago" % (years, months)
            else:
                return str(years) + " years ago"
    #Otherwise, just years
    return str((delta + 183) / 365) + " years ago"
