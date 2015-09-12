# -*- coding: utf-8 -*-
import json

from vilya.libs.rdstore import rds
from vilya.models.utils import CJsonEncoder, to_timestamp
from vilya.libs.signals import rds_pub_signal

MAX_MESSAGE_COUNT = 1989
LATEST_MESSAGE_NUM = 50
RDS_ROOM_KEY = "chat:room:%s"


class Message(object):

    def __init__(self, db_key):
        self.db_key = db_key

    @classmethod
    def get(cls, db_key):
        return cls(db_key=db_key)

    def add_message(self, message_data):
        data = json.dumps(message_data, cls=CJsonEncoder)
        rds.zadd(self.db_key, data, to_timestamp(message_data.get('date')))
        rds.zremrangebyrank(self.db_key, 0,  -1 * (MAX_MESSAGE_COUNT + 1))
        rds_pub_signal.send('add_message',
                            data=data,
                            channel=self.db_key)

    def get_messages(self, start=0, stop=LATEST_MESSAGE_NUM):
        data = rds.zrevrange(self.db_key, start, stop)
        return reversed([json.loads(d) for d in data])

    def delete_by_key(self):
        rds.delete(self.db_key)


def get_room_message(room_name):
    return Message.get(db_key=RDS_ROOM_KEY % room_name)
