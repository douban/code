# -*- coding: utf-8 -*-

import json

from tasks import fetch_mirror_project
from vilya.views.util import require_login_json, error_message

_q_exports = []


def _q_lookup(request, proj_id):
    if request.method == "POST":
        return fetch(request, proj_id)
    return error_message("bad request")


@require_login_json
def fetch(request, proj_id):
    fetch_mirror_project(proj_id)
    return json.dumps({"ok": 1})
