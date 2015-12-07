# -*- coding: utf-8 -*-

from vilya.models.trello.wrapper import DoubanTrelloClient
from vilya.models.utils import parse_trello_card_code
from trolly.card import Card
from vilya.config import DOMAIN

from vilya.libs.mq import async


@async
def process_trello_notify(user, ticket):
    if not ticket or not user or not user.trello_access_token:
        return

    card_id = parse_trello_card_code(ticket.description)
    if card_id:
        _notify(user, ticket, card_id)


def _notify(user, ticket, card_id):
    client = DoubanTrelloClient(user.trello_access_token['oauth_token'])
    card = Card(client, card_id)
    tmpl = "Attention: %s has submitted a Pull Request. %s"
    card.addComments(tmpl % (user.name, '%s%s' % (DOMAIN, ticket.url)))
