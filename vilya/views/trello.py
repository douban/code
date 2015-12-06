# coding=utf8

__author__ = 'torpedoallen'

from quixote.errors import AccessError, TraversalError
from vilya.models.trello.wrapper import DoubanTrelloClient
from vilya.config import DOMAIN

_q_exports = ['bind', 'unbind']


def _q_access(request):
    if not request.user:
        raise AccessError('must login')


def bind(request):
    user = request.user
    if user.trello_access_token:
        raise TraversalError('already binded')
    dtclient = DoubanTrelloClient()
    if not user.trello_request_token:
        # get request token
        request_token = dtclient.get_request_token()
        user.trello_request_token = request_token

        # authorize
        url = '%s%s' % (DOMAIN, request.environ.get('REQUEST_URI'))
        authorize_url = dtclient.get_authorisation_url(
            request_token['oauth_token'], url)
        return request.redirect(authorize_url)
    else:
        # get access token
        oauth_verifier = request.get_form_var("oauth_verifier")
        access_token = dtclient.get_access_token(
            user.trello_request_token, oauth_verifier)
        user.trello_access_token = access_token
        url = '%s%s' % (DOMAIN, user.url)
        return request.redirect(url)


def unbind(request):
    user = request.user
    user.trello_request_token = None
    user.trello_access_token = None
    url = '%s%s' % (DOMAIN, user.url)
    return request.redirect(url)
