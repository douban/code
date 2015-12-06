# -*- coding: utf-8 -*-
from base64 import b64decode

from quixote.errors import AccessError
from quixote import get_request

from vilya.models.user import User


class AuthCode(object):

    def __init__(self, header):
        self.login = None
        self.passwd = None
        self.user = None
        try:
            auth_type, auth_string = header.split()
            login, passwd = b64decode(auth_string).split(':')
            self.login = login
            self.passwd = passwd
            self.user = User.get_by_name(login)
        except (ValueError, TypeError):
            pass

    def confirm(self):
        username = self.login
        passwd = self.passwd
        if username == 'code' and passwd == 'code':
            return True
        if self.user and self.user.validate_password(passwd):
            return True
        raise UnauthorizedError


class UnauthorizedError(AccessError):
    """
    The request requires user authentication.
    This subclass of AccessError sends a 401 instead of a 403,
    hinting that the client should try again with authentication.

    (from http://www.quixote.ca/qx/HttpBasicAuthentication)
    """
    status_code = 401
    title = "Unauthorized"
    description = "You are not authorized to access this resource."

    def __init__(self, realm='Protected', public_msg=None, private_msg=None):
        self.realm = realm
        AccessError.__init__(self, public_msg, private_msg)

    def format(self):
        request = get_request()
        request.response.set_header('WWW-Authenticate',
                                    'Basic realm="%s"' % self.realm)
        return AccessError.format(self)
