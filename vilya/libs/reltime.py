# -*- coding: utf-8 -*-

import time

from vilya.libs.text import plural


def compute_relative_time(timestamp=1340875790):
    #git/data.c void show_date_relative
    delta = int(time.time()) - int(timestamp)
    # In unitests we have 0 or 1 seconds, not stable,
    # better say 'few' when below 10 s.
    if delta < 10:
        return "few seconds ago"
    if delta < 90:
        return str(delta) + " seconds ago"

    chunks = (
        (60 * 60 * 24 * 365, lambda n: plural(n, 'year', 'years')),
        (60 * 60 * 24 * 30, lambda n: plural(n, 'month', 'months')),
        (60 * 60 * 24 * 7, lambda n: plural(n, 'week', 'weeks')),
        (60 * 60 * 24, lambda n: plural(n, 'day', 'days')),
        (60 * 60, lambda n: plural(n, 'hour', 'hours')),
        (60, lambda n: plural(n, 'minute', 'minutes'))
    )

    for i, (seconds, name) in enumerate(chunks):
        count = delta // seconds
        if count != 0:
            break

    s = '{0} {1}'.format(count, name(count))

    if i + 1 < len(chunks):
        seconds2, name2 = chunks[i + 1]
        count2 = (delta - (seconds * count)) // seconds2
        if count2 != 0:
            s += ' {0} {1}'.format(count2, name2(count2))
    return s + ' ago'
