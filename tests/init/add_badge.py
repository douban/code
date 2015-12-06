from vilya.models.badge import Badge

import os
dir = os.path.join(os.path.dirname(__file__), '../../hub/static/img/badges/')
badge_number = len(os.listdir(dir))

badge = Badge.add('code', 'Code Developer')
badge.award('testuser')
badge.award('qingfeng')

badge2 = Badge.add('bugslayer', 'Bug Slayer')
badge2.award('testuser')


for idx in xrange(2, badge_number):
    badge = Badge.add("badge%s" % idx, "Badge %s" % idx)
    badge.award('testuser')
