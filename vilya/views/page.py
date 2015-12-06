# -*- coding: utf-8 -*-

from __future__ import absolute_import

from vilya.libs.template import st

_q_exports = ['promo_proj']


def promo_proj(request):
    promo_projs = {
        "Vagrant": {
            "image": "http://t.douban.com/view/status/raw/public/82670450897abd1.jpg",  # noqa
            "title": "Shire in Vagrant",
            "description": u"搭建开发环境<br>从未如此轻松",
            "url": "http://theoden.intra.douban.com:45068/siv/index.html",
        },
        "code": {
            "image": "http://img3.douban.com/mpic/s10482437.jpg",
            "title": "Code",
            "description": u"Code开发者招募中",
            "url": "http://code.dapps.douban.com/code",
        },
        "codecli": {
            "image": "http://pastebin.dapps.douban.com/image/86/6386_raw.png",
            "title": "codecli",
            "description": u"codecli 帮你玩转 pullreq",
            "url": "http://code.dapps.douban.com/codecli",
        },
        "MoGit": {
            "image": "http://pastebin.dapps.douban.com/image/30/6930_raw.png",
            "title": "MoGit",
            "description": u"设计师也能享受Code",
            "url": "http://code.dapps.douban.com/bear/mogit/docs/pages/index.html",  # noqa
        },
        "P": {
            "image": "http://p.dapps.douban.com/i/0d433de4ae8211e2b5e424b6fdf76328.png",  # noqa
            "title": "P",
            "description": u"快速简单的分享图片",
            "url": "http://p.dapps.douban.com/",
        },
    }

    from random import sample
    promo_proj = promo_projs[sample(promo_projs.keys(), 1)[0]]
    return st('page/promo_proj.html', **locals())
