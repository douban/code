# -*- coding: utf-8 -*-

import json
from vilya.libs.auth.decorators import login_required
from vilya.libs.template import st

_q_exports = ['setting', ]


@login_required
def _q_index(request):
    user = request.user
    return st('settings/notification.html', **locals())


@login_required
def setting(request):
    is_on = request.get_form_var('is_on')
    notifications_meta = request.get_form_var('notifications_meta')
    user = request.user
    result = "success"
    try:
        user.settings.__setattr__(notifications_meta, is_on)
    except Exception:
        result = "fail"
    return json.dumps({"result": result})
