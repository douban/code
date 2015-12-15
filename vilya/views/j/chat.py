# -*- coding: utf-8 -*-

from datetime import datetime
from vilya.libs.template import st
from vilya.models.message import get_room_message
from vilya.models.room import Room
from vilya.views.util import jsonize, render_message

_q_exports = ['delete_room']


@jsonize
def _q_lookup(request, room_name):
    if request.method == "POST":
        content = request.get_form_var('message')
        author = request.user.username
        date = datetime.now()
        message_data = {
            "content": content,
            "author": author,
            "date": date
        }
        room_message = get_room_message(room_name)
        room_message.add_message(message_data)
        return {'r': 1}
    if request.method == "GET":
        if room_name != 'lobby' and not Room.exists(room_name):
            return {'r': 0, 'msg': 'room not exists'}
        room_message = get_room_message(room_name)
        messages = room_message.get_messages()
        render_messages = [render_message(m) for m in messages]
        return {'r': 1, 'msg': render_messages}


@jsonize
def delete_room(request):
    room_name = request.get_form_var('room_name', '')
    if Room.delete(room_name):
        get_room_message(room_name).delete_by_key()
        return {'r': 1, 'msg': '删除成功'}

    return {'r': 0, 'msg': '删除失败, 可能该room已被删除'}
