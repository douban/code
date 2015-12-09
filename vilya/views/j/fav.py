# -*- coding: utf-8 -*-

from vilya.models.user_fav import UserFavItem
from vilya.models.consts import K_PULL, K_ISSUE
from vilya.views.util import jsonize

_q_exports = []


@jsonize
def _q_index(request):
    user = request.user
    tid = request.get_form_var('tid', '')
    tkind = request.get_form_var('tkind', '0')
    tkind = int(tkind)
    if not user or tkind not in [K_PULL, K_ISSUE]:
        return {'r': 1}
    if request.method == "POST":
        UserFavItem.add(user.username, tid, tkind)
    elif request.method == 'DELETE':
        UserFavItem.delete_by_user_target_kind(user.username, tid, tkind)
    else:
        return {'r': 1}
    return {'r': 0}
