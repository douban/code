# -*- coding: utf-8 -*-

import re
import json
import uuid
from time import mktime
from datetime import datetime, date


class CJsonEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        else:
            return json.JSONEncoder.default(self, obj)


def linear_normalized(data):
    min_val = min(data or [0, ])
    max_val = max(data or [0, ])
    if min_val == max_val:
        return [0.5 for i in data]
    return [(d - min_val) / (max_val - min_val) for d in data]


def get_uuid():
    return str(uuid.uuid4())


def to_timestamp(date):
    assert isinstance(date, datetime)
    return mktime(date.timetuple())


class _Missing(object):

    def __repr__(self):
        return 'no value'

    def __reduce__(self):
        return '_missing'

_missing = _Missing()


if __name__ == "__main__":
    import doctest
    doctest.testmod()
