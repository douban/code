# -*- coding: utf-8 -*-

from django.http import HttpResponse
from vilya.libs.template import st


def index(request):
    return HttpResponse("Hello, world. You're at the vilya index.")


def mirrors(request):
    from vilya.models.project import CodeDoubanProject
    your_projects = CodeDoubanProject.get_projects(
        owner="mirror", sortby='sumup')
    return HttpResponse(st('/mirrors.html', **locals()))
