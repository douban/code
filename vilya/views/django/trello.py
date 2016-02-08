# -*- coding: utf-8 -*-

from django.http import HttpResponseRedirect
from django.http import HttpResponseBadRequest
from vilya.config import DOMAIN


def bind(request):
    from vilya.models.trello.wrapper import DoubanTrelloClient
    user = request.user
    if user.trello_access_token:
        return HttpResponseBadRequest('already binded')

    dtclient = DoubanTrelloClient()
    if not user.trello_request_token:
        # get request token
        request_token = dtclient.get_request_token()
        user.trello_request_token = request_token

        # authorize
        url = '%s%s' % (DOMAIN, request.environ.get('REQUEST_URI'))
        authorize_url = dtclient.get_authorisation_url(
            request_token['oauth_token'], url)
        return HttpResponseRedirect(authorize_url)
    else:
        # get access token
        oauth_verifier = request.GET.get("oauth_verifier")
        access_token = dtclient.get_access_token(
            user.trello_request_token, oauth_verifier)
        user.trello_access_token = access_token
        url = '%s%s' % (DOMAIN, user.url)
        return HttpResponseRedirect(url)


def unbind(request):
    user = request.user
    user.trello_request_token = None
    user.trello_access_token = None
    url = '%s%s' % (DOMAIN, user.url)
    return HttpResponseRedirect(url)
