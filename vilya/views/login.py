# coding=utf-8
import json

from vilya.libs.template import st
from vilya.models.user import User, set_user

_q_exports = []


def _q_index(request):
    if request.method == 'POST':
        name = request.get_form_var('username')
        password = request.get_form_var('password')
        user = User.get_by_name(name)
        if user and user.validate_password(password):
            continue_url = request.get_form_var(
                'continue', '') or request.get_form_var('Referer', '')
            request.user = user
            set_user(user.id)
            return json.dumps({"r": 0, "continue": continue_url or "/"})
        else:
            message = '用户名或密码错误！'
            return json.dumps({"r": 1, 'message': message})
    return st('login.html')
