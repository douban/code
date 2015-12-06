# -*- coding: utf-8 -*-
from vilya.libs.template import st
from vilya.models.project import CodeDoubanProject


_q_exports = []


def _q_index(request):
    your_projects = CodeDoubanProject.get_projects(
        owner="mirror", sortby='sumup')
    return st('/mirrors.html', **locals())
