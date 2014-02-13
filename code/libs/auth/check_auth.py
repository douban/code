# -*- coding: utf-8 -*-

from datetime import datetime
from code.libs.auth.oauth import OAuthError
from code.libs.auth import errors as err
from code.libs.auth import AuthCode


def check_auth(request):
    auth_header = request.environ.get('HTTP_AUTHORIZATION')

    # 无 Token 直接返回
    if not auth_header:
        return

    # Token 格式是否正确
    if not auth_header.startswith('Bearer '):
        # raise OAuthError(*err.auth_access_token_is_missing)
        # 考虑到需要兼容 qaci 使用 Basic auth 的场景，先不 raise
        auth = AuthCode(auth_header)
        if auth.confirm():
            request.user = auth.user
        return

    oauth_token = auth_header[7:]
    token = ApiToken.get_by_token(oauth_token)

    # ApiToken 是否存在
    if not token:
        raise OAuthError(*err.auth_invalid_access_token)

    # ApiToken 是否过期
    if datetime.now() > token.expire_time:
        raise OAuthError(*err.auth_access_token_has_expired)

    request.user = token.user
    request.client_id = token.client_id
