# -*- coding: utf-8 -*-
from functools import wraps

from vilya.config import LOGIN_URL
from vilya.libs.auth.views import redirect_to_login

REDIRECT_FIELD_NAME = 'continue'


def user_passes_test(test_func, login_url=LOGIN_URL,
                     redirect_field_name=REDIRECT_FIELD_NAME):

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if test_func(request.user):
                return view_func(request, *args, **kwargs)
            return redirect_to_login(request, request.url, login_url,
                                     redirect_field_name)
        return _wrapped_view
    return decorator


def login_required(func=None, redirect_field_name=REDIRECT_FIELD_NAME,
                   login_url=LOGIN_URL):
    decorator = user_passes_test(
        lambda user: user is not None,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if func:
        return decorator(func)
    return decorator
