# -*- coding: utf-8 -*-
import json
import urllib
from datetime import datetime
from quixote.errors import TraversalError, PublishError

from vilya.models.user import User
from vilya.models.api_key import ApiKey
from vilya.models.api_token import ApiToken
from vilya.libs.auth.oauth import OAuthCode, OAuthConfirm
from vilya.libs.auth import errors as err
from vilya.libs.template import request, st
from vilya.config import DEVELOP_MODE

GRANT_TYPE_AUTHORIZATION_CODE = 'authorization_code'
GRANT_TYPE_REFRESH_TOKEN = 'refresh_token'
GRANT_TYPE_PASSWORD = 'password'

_q_exports = ['authorize', 'token']


def _q_index(request):
    raise TraversalError()


def authorize(request):
    client_id = __check_request_required_var('client_id')
    redirect_uri = __check_request_required_var('redirect_uri')
    response_type = __check_request_required_var('response_type')
    refuse = request.get_form_var('refuse')
    state = request.get_form_var('state', '')
    cid = request.get_form_var('cid', '')

    connector = '?' if redirect_uri.find('?') == -1 else '&'

    if refuse:
        return request.redirect("%s%serror=access_denied" % (redirect_uri,
                                                             connector))

    if not request.user:
        return __login_authorize(request, client_id, redirect_uri,
                                 response_type, state)

    apikey = ApiKey.get_by_client_id(client_id)

    if not apikey:
        raise InvalidRequest(err.invalid_apikey, ext=client_id)

    if apikey.status == ApiKey.STATUS_BLOCKED:
        raise InvalidRequest(err.apikey_blocked, ext=client_id)

    if apikey.status != ApiKey.STATUS_DEV:
        if apikey.redirect_uri != redirect_uri:
            raise InvalidRequest(err.redirect_uri_mismatch, ext=redirect_uri)

    user_id = request.user.username
    if request.method == 'POST' and OAuthConfirm.confirm(user_id, cid):
        code = OAuthCode(apikey.client_id, user_id).code
        params = dict(code=code, state=state)
        return request.redirect("%s%s%s" % (redirect_uri,
                                            connector,
                                            urllib.urlencode(params)))

    cid = OAuthConfirm(user_id).cid
    return st('/oauth_confirm.html', **dict(request=request,
                                            cid=cid,
                                            apikey=apikey))


def token(request):
    method = request.method
    if method != 'POST':
        raise InvalidRequest(err.invalid_request_method, ext=method)

    client_id = __check_request_required_var('client_id')
    client_secret = __check_request_required_var('client_secret')
    grant_type = __check_request_required_var('grant_type')

    apikey = ApiKey.get_by_client_id(client_id)

    if not apikey:
        raise InvalidRequest(err.invalid_apikey, ext=client_id)

    if apikey.client_secret != client_secret:
        raise InvalidRequest(err.client_secret_mismatch, ext=client_secret)

    if grant_type == GRANT_TYPE_AUTHORIZATION_CODE:
        return __token_grant_by_authorization_code(apikey)

    if grant_type == GRANT_TYPE_REFRESH_TOKEN:
        return __token_grant_by_refresh_token(apikey)

    if grant_type == GRANT_TYPE_PASSWORD:
        return __token_grant_by_password(apikey)


def __login_authorize(request, client_id, redirect_uri, response_type, state):
    params = dict(client_id=client_id, redirect_uri=redirect_uri,
                  response_type=response_type, state=state)
    login_url = request.get_url() + '?' + urllib.urlencode(params)
    return request.redirect(login_url)


def __check_request_required_var(name):
    ret = request.get_form_var(name)
    if ret:
        return ret
    raise InvalidRequest(err.required_parameter_is_missing, ext=name)


def __token_grant_by_authorization_code(apikey):
    redirect_uri = __check_request_required_var('redirect_uri')
    authorization_code = __check_request_required_var('code')

    if apikey.status != ApiKey.STATUS_DEV:
        if apikey.redirect_uri != redirect_uri:
            raise InvalidRequest(err.redirect_uri_mismatch, ext=redirect_uri)

    user_id = OAuthCode.check(apikey.client_id, authorization_code)
    if not user_id:
        raise InvalidRequest(
            err.invalid_authorization_code, ext=authorization_code)

    request.response.set_content_type('application/json; charset=utf8')

    token = ApiToken.add(apikey.client_id, user_id)
    return json.dumps(token.token_dict())


def __token_grant_by_refresh_token(apikey):
    refresh_token = __check_request_required_var('refresh_token')

    token = ApiToken.get_by_refresh_token(refresh_token)
    if not token:
        raise InvalidRequest(err.invalid_refresh_token, ext=refresh_token)

    if datetime.now() > token.refresh_expire_time:
        raise InvalidRequest(err.refresh_token_has_expired, ext=refresh_token)

    new_token = token.refresh()
    return json.dumps(new_token.token_dict())


def __token_grant_by_password(apikey):
    username = __check_request_required_var('username')
    password = __check_request_required_var('password')
    user = User.get_by_name(username)
    if not DEVELOP_MODE and user and not user.validate_password(password):
        raise InvalidRequest(err.username_password_mismatch)

    token = ApiToken.add(apikey.client_id, username)
    return json.dumps(token.token_dict())


class InvalidRequest(PublishError):

    def __init__(self, oauth2_error, ext=None, status_code=400):
        self.private_msg = None
        self.public_msg = None
        self.status_code = status_code
        self.error_code = oauth2_error[0]
        self.message = oauth2_error[1]
        self.title = 'invalid_request'
        if ext:
            self.message = self.message % ext
        self.description = 'error_code:%s, %s' % (
            self.error_code, self.message)


def _q_exception_handler(request, exception):
    if not isinstance(exception, InvalidRequest):
        raise exception

    if request.get_path() == '/oauth/authorize':
        request.response.set_content_type('text/html; charset=utf-8')
        raise exception
    else:
        request.response.set_content_type('application/json; charset=utf-8')
        error = dict(code=exception.error_code,
                     msg=exception.message,
                     request='%s: %s' % (request.method,
                                         request.url))
        return json.dumps(error)
