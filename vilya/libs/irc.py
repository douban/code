# -*- coding: utf-8 -*-
import socket

from vilya.libs.mq import async
from vilya.config import IRC_SERVER, IRC_PORT


def netcat(hostname, port, content):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((hostname, port))
    s.sendall(content)
    s.shutdown(socket.SHUT_WR)
    while 1:
        data = s.recv(1024)
        if data == "":
            break
    s.close()


def _send_message(channel, message):
    lines = []
    if isinstance(channel, list):
        channel = ','.join(channel)
    for line in message.split('\n'):
        line = line.strip()
        if not line:
            continue
        lines.append('%s %s' % (channel, line))

    if lines:
        netcat(IRC_SERVER, IRC_PORT, '\n'.join(lines))


@async
def send_message(channel, message):
    _c = channel
    _m = message
    if isinstance(channel, unicode):
        _c = channel.encode('utf-8')
    if isinstance(message, unicode):
        _m = message.encode('utf-8')

    return _send_message(_c, _m)


class IrcMsg(object):
    def __init__(self, to, msg):
        self.to = [to, ] if isinstance(to, basestring) else to
        self.msg = msg

    @staticmethod
    def irc_receiver_filter(receivers, target):
        from vilya.models.user import User
        rs = set()
        for receiver in receivers:
            user = User(receiver)
            if user and user.notify_irc(target):
                rs.add(receiver)
        return rs

    def send(self):
        if self.to:
            for user in self.to:
                send_message(user, self.msg)


def notify_by_irc(target_obj, channel, message):
    from vilya.models.user import User
    user = User(channel)
    notify_irc = user.notify_irc(target_obj) if user else None
    if notify_irc:
        send_message(channel, message)
