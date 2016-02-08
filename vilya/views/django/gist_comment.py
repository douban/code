# -*- coding: utf-8 -*-

from django.http import HttpResponse
from django.http import JsonResponse
from django.http import HttpResponseRedirect
from django.http import StreamingHttpResponse
from django.http import HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from vilya.libs.template import st


@csrf_exempt
def index(request, username, id):
    from vilya.models.user import User
    from vilya.models.gist import Gist
    from vilya.models.gist_comment import GistComment

    django_user = request.user
    # FIXME(xutao) translate django user to quixote user
    user = User('xutao881001')
    request.user = user
    gist = Gist.get(id)

    if request.method == 'POST':
        content = request.POST.get('content', '')
        if content:
            GistComment.add(gist.id, request.user.username, content)
    return HttpResponseRedirect(gist.url)


@csrf_exempt
def comment(request, username, id, comment_id):
    from vilya.models.user import User
    from vilya.models.gist import Gist
    from vilya.models.gist_comment import GistComment

    django_user = request.user
    # FIXME(xutao) translate django user to quixote user
    user = User('xutao881001')
    request.user = user
    gist = Gist.get(id)

    if request.method == 'POST':
        act = request.POST.get('act', None)
        if act and act in ('delete', 'update'):
            comment = GistComment.get(comment_id)
            if act == 'delete' and comment:
                if comment.can_delete(request.user.username):
                    comment.delete()
                    return JsonResponse({'r': 1})
                raise HttpResponseForbidden(
                    "Unable to delete comment %s" % comment_id)
    return HttpResponseRedirect(gist.url)
