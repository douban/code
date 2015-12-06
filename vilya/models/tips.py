# -*- coding: utf-8 -*-

import random

tips = (
    (u'用f这个快捷键就可以fork项目了哦', ''),
    (u'用p这个快捷键就可以发起pullrequest了哦', ''),
    (u'Code上的项目现在已经有了Hook功能了,你是否尝试过?', '/code/hooks'),
    (u'Code的徽章系统已经上线了', '/people/qingfeng/'),
    (u'Code上面已经可以看到代码提交频次的图表了', '/code/graph'),
    (u'Code上面已经可以看到项目的贡献者列表了', '/code/graph'),
    (u'用@可以搜索人', ''),
    (u'现在可以做commit的compare了,到source里就可以找到哦', ''),
    (u'加入Code开发!', '/code/source/blob/master/README.md'),
    (u'现在都有哪些徽章?', '/badge/all'),
    (u'在源码页按下t试试看', '/code/'),
    (u'新的组织页上线,快去看看吧', '/hub/projects'),
)


class Tips(object):
    @classmethod
    def get_tip(cls):
        return random.sample(tips, 1)[0]
