# -*- coding: utf-8 -*-

from django.http import JsonResponse
from django.http import HttpResponseRedirect
from django.http import HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def index(request, username, id):
    from vilya.models.gist import Gist
    from vilya.models.gist_comment import GistComment

    user = request.user
    gist = Gist.get(id)

    if request.method == 'POST':
        content = request.POST.get('content', '')
        if content:
            GistComment.add(gist.id, user.username, content)
    return HttpResponseRedirect(gist.url)


@csrf_exempt
def comment(request, username, id, comment_id):
    from vilya.models.gist import Gist
    from vilya.models.gist_comment import GistComment

    user = request.user
    gist = Gist.get(id)

    if request.method == 'POST':
        act = request.POST.get('act', None)
        if act and act in ('delete', 'update'):
            comment = GistComment.get(comment_id)
            if act == 'delete' and comment:
                if comment.can_delete(user.username):
                    comment.delete()
                    return JsonResponse({'r': 1})
                raise HttpResponseForbidden("Unable to delete comment %s" % comment_id)
    return HttpResponseRedirect(gist.url)
