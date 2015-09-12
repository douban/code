# -*- coding: utf-8 -*-
import re

from vilya.models.room import Room
from vilya.models.message import get_room_message
from vilya.libs.template import st

_q_exports = ['add_room']


def _q_index(request):
    user = request.user
    if not user:
        return request.redirect("/")
    all_rooms = Room.get_all_rooms()
    messages = get_room_message('lobby').get_messages()
    return st("chat.html", **locals())


def add_room(request):
    user = request.user
    if not user:
        return request.redirect("/")

    name = request.get_form_var('name', '')
    owner = user.username

    error = ""
    if request.method == "POST":
        rooms = Room.get_all_rooms()
        name_pattern = re.compile(r'[a-zA-Z0-9\_]*')
        if not name:
            error = "name_not_exists"
        elif name != re.findall(name_pattern, name)[0]:
            error = "invilid_name"
        elif len(name) > 10:
            error = "too_long_name"
        elif name in ([room.name for room in rooms]+['lobby', 'Lobby']):
            error = "name_existed"
        else:
            room = Room.add(name, owner)
            return request.redirect("/hub/chat")
    return st('add_room.html', **locals())
