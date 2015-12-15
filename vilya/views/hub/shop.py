# encoding: utf-8
from vilya.libs.template import st


_q_exports = []


def _q_index(request):
    t_shirts = [
        ['1994842254', 'normal系'],
        ['1994842218', '黑色系'],
        ['1994842153', '粉色系'],
        ['1994842093', '低调系'],
    ]
    return st('shop.html', **locals())
