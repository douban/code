# -*- coding: utf-8 -*-

import pickle

from vilya.models.feed import get_public_feed


with open('tests/init/feed_actions.pickle', 'r') as f:
    actions = pickle.load(f)


feed = get_public_feed()
if feed:
    for action in actions:
        feed.add_action(action)
