import time

from tests.base import TestCase
from vilya.models.notification import Notification, rds_key_for_receiver
from vilya.libs.rdstore import rds


class TestNotification(TestCase):

    def setUp(self):
        self.test_user1 = "testuser_for_test"
        self.test_user2 = "testuser_for_test2"
        self.receivers = [self.test_user1, self.test_user2]
        self.uids = [self.gen_uid() for i in range(50)]

    def tearDown(self):
        rds.delete(rds_key_for_receiver(self.test_user1))
        rds.delete(rds_key_for_receiver(self.test_user2))

    def gen_uid(self):
        t = time.time()
        t1 = int(t)
        t2 = int((t-t1)*10E6)
        time.sleep(0.01)
        return "%x%x" % (t1, t2)

    def test_add_notification(self):
        data = {'data': 'some data here'}
        for i, uid in enumerate(self.uids[:10], start=1):
            Notification(uid, self.receivers, data).send()
            assert len(Notification.get_data(self.test_user1)) == i
            assert Notification.unread_count(self.test_user1) == i
            assert len(Notification.get_data(self.test_user2)) == i
            assert Notification.unread_count(self.test_user2) == i

    def test_mark_as_read(self):
        data = {'data': 'some data here'}
        for uid in self.uids:
            Notification(uid, self.receivers, data).send()

        to_mark_as_read = self.uids[:5] + self.uids[20:30] + self.uids[40:50]

        for i, uid in enumerate(to_mark_as_read, start=1):
            Notification.mark_as_read(self.test_user1, uid)
            assert Notification.unread_count(self.test_user1) == 50-i

        assert Notification.unread_count(self.test_user2) == 50
        Notification.mark_all_as_read(self.test_user2)
        assert Notification.unread_count(self.test_user2) == 0

    def test_get_data(self):
        for i, uid in enumerate(self.uids[:10], start=1):
            data = {'data': 'test' + uid}
            Notification(uid, self.receivers, data).send()

        data = Notification.get_data(self.test_user1)
        assert len(data) == 10
        for i, d in enumerate(reversed(data)):
            assert d.get('uid') == self.uids[i]
            assert d.get('data') == 'test'+self.uids[i]
