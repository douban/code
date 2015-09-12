# -*- coding: utf-8 -*-

import json
from vilya.libs.template import st

_q_exports = ['setting', ]


def _q_index(request):
    user = request.user
    return st('settings/codereview.html', **locals())


def setting(request):
    is_enable = request.get_form_var('is_enable')
    field = request.get_form_var('field')
    user = request.user
    result = "success"
    origin = user.settings.__getattr__(field)
    try:
        user.settings.__setattr__(field, is_enable)
    except Exception:
        result = "fail"
    return json.dumps({"result": result, "origin": origin})
