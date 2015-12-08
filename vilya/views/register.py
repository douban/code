# coding=utf-8
import json

from vilya.libs.template import st
from vilya.models.nuser import User2 as CodeUser
from vilya.models.user import set_user

_q_exports = []


def _q_index(request):
    if request.method == 'POST':
        email = request.get_form_var('email')
        password = request.get_form_var('password')
        if not email:
            return json.dumps({'r': 1, 'message': 'Email没有指定'})
        user_name = email.split('@')[0]
        if CodeUser.is_exists(user_name):
            return json.dumps({'r': 1, 'message': '用户已存在'})
        code_user = CodeUser.add(user_name, password)
        set_user(code_user.id)
        return json.dumps({'r': 0})
    return st('register.html')
