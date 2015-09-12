# -*- coding: utf-8 -*-

from datetime import datetime
from tests.base import TestCase
from vilya.models.feed import (
    Feed, get_user_inbox, get_user_feed, get_public_feed)


TEST_ACTION_TYPE = 'code_review'


class TestFeed(TestCase):

    def test_feed(self):
        key = 'testkey'
        feed = Feed.get(key)
        assert feed is not None
        # feed.add_action will run blinker connect `@rds_pub_signal.connect`,
        #   and render a piece of mako template
        feed.add_action({
            'type': TEST_ACTION_TYPE,
            'content': 'content',
            'date': datetime.now(),
        })
        feed = feed.get(key)
        actions = feed.get_actions()
        assert actions is not None
        assert len(actions) == 1
        assert actions[0]['type'] == TEST_ACTION_TYPE
        assert actions[0]['content'] == 'content'

    def test_userinbox(self):
        actor = 'testuser1'
        all_feed = [
            get_user_inbox(actor),
            get_user_feed(actor),
            get_public_feed(),
        ]
        data = dict(type='pull_request',
                    owner='testuser2',
                    url='',
                    title='pr title',
                    description='pr desc',
                    date=datetime.now(),
                    from_proj='10',
                    to_proj='1',
                    uid='pullrequest-1-1-unmerge')
        for feed in all_feed:
            feed.add_action(data)
            actions = feed.get_actions()
            assert len(actions) == 1
