# coding=utf8

import urlparse
import oauth2 as oauth
from trolly.client import Client

from vilya.config import (
    TRELLO_CONSUMER_KEY as CONSUMER_KEY,
    TRELLO_CONSUMER_SECRET as CONSUMER_SECRET
)

# APP_NAME = 'TODO & FIXME'
APP_NAME = 'Code Tells Trello'
REQUEST_TOKEN_URL = 'https://trello.com/1/OAuthGetRequestToken'
ACCESS_TOKEN_URL = 'https://trello.com/1/OAuthGetAccessToken'
AUTHORIZE_URL = 'https://trello.com/1/OAuthAuthorizeToken'


class DoubanTrelloClient(Client):

    def __init__(self, token=None):
        super(DoubanTrelloClient, self).__init__(
            CONSUMER_KEY, user_auth_token=token)
        self.consumer = oauth.Consumer(CONSUMER_KEY, CONSUMER_SECRET)

    def get_authorisation_url(self, oauth_token, return_url):
        query_params = {
            'name': APP_NAME,
            'expiration': 'never',
            'scope': 'read,write,account',
            'oauth_callback': return_url,
            'oauth_token': oauth_token,
        }

        authorisation_url = self.buildUri(
            path='/OAuthAuthorizeToken',
            query_params=query_params
        )

        return authorisation_url

    def get_request_token(self):
        client = oauth.Client(self.consumer)
        resp, content = client.request(REQUEST_TOKEN_URL, "GET")
        if resp['status'] != '200':
            raise Exception("Invalid response %s." % resp['status'])
        request_token = dict(urlparse.parse_qsl(content))
        return request_token

    def get_access_token(self, request_token, oauth_verifier):
        token = oauth.Token(
            request_token['oauth_token'], request_token['oauth_token_secret'])
        token.set_verifier(oauth_verifier)
        client = oauth.Client(self.consumer, token)
        resp, content = client.request(ACCESS_TOKEN_URL, "POST")
        access_token = dict(urlparse.parse_qsl(content))
        return access_token


if __name__ == "__main__":
    TOKEN = '2f68a34c08c39cb97df184ef3f13df1a72ed3aadb0e19e12c25768ff8ab1b51e'  # noqa
    client = DoubanTrelloClient()
    print client.get_authorisation_url('22222', 'http://www.douban.com')
    #client = DoubanTrelloClient(token=TOKEN)
    #_list = List(client, '50e2df09d07cc81d15002d7a')
    # print _list.getCards()
