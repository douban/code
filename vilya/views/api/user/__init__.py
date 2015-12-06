# -*- coding: utf-8 -*-

from vilya.views.api.utils import api_require_login, api_list_user, jsonize
from vilya.models.project import CodeDoubanProject

_q_exports = ['following', 'followers', 'repos']


@api_require_login
@jsonize
def _q_index(request):
    user = request.user.as_dict()
    user["projects_count"] = CodeDoubanProject.count_by_owner_id(
        request.user.username)
    return user


@api_require_login
@jsonize
def followers(request):
    followers = request.user.get_followers()
    return api_list_user(followers)


@api_require_login
@jsonize
def repos(request):
    projects = CodeDoubanProject.get_projects(owner=request.user.username)
    return [project.as_dict() for project in projects]
