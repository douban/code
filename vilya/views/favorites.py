# -*- coding: utf-8 -*-

from vilya.libs.template import st
from vilya.models.user_fav import UserFavItem

_q_exports = []


def _q_index(request):
    if not request.user:
        return request.redirect('/')
    favs = UserFavItem.gets_by_user_kind(request.user.username)
    return st('/favorites.html', **locals())
