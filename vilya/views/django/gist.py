# -*- coding: utf-8 -*-

from django.http import HttpResponse
from django.http import JsonResponse
from django.http import HttpResponseRedirect
from django.http import StreamingHttpResponse
from django.http import HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from vilya.libs.template import st


@csrf_exempt
def index(request):
    from vilya.views.util import is_mobile_device
    from vilya.models.user import User
    from vilya.models.gist import Gist
    django_user = request.user
    # FIXME(xutao) translate django user to quixote user
    user = User('xutao881001')
    request.user = user
    if request.method == 'POST':
        desc, is_public, names, contents, oids = _get_req_gist_data(request)
        owner_id = user and user.username or Gist.ANONYMOUS
        gist = Gist.add(desc, owner_id, is_public, names, contents)
        return HttpResponseRedirect(gist.url)

    tdt = dict(request=request, gists=[], user=user)
    if user:
        gists = Gist.gets_by_owner(user.username, limit=4)
        tdt.update(dict(gists=gists))

    if is_mobile_device(request):
        return HttpResponse(st('/m/gist/index.html', **tdt))
    return HttpResponse(st('/gist/index.html', **tdt))


def discover(request):
    return _discover(request)


def forked(request):
    return _discover(request)


def starred(request):
    return _discover(request)


def _get_req_gist_data(request):
    _form = request.POST
    desc = _form.get('desc', '')
    is_public = _form.get('gist_public', '1')
    gist_names = _form.getlist('gist_name', '')
    gist_contents = _form.getlist('gist_content', '')
    gist_oids = _form.getlist('oid', '')
    return (desc, is_public, gist_names, gist_contents, gist_oids)


def _discover(request):
    import inspect
    from vilya.models.user import User
    from vilya.models.gist import Gist
    django_user = request.user
    # FIXME(xutao) translate django user to quixote user
    user = User('xutao881001')
    request.user = user

    name = inspect.stack()[1][3]
    (page, start, link_prev, link_next, sort,
     direction) = make_page_args(request, name)
    gists = Gist.discover(name, sort, direction, start)
    tdt = dict(
        request=request,
        gists=gists,
        page=page,
        link_prev=link_prev,
        link_next=link_next,
        sort=sort,
        direction=direction,
        user=user
    )
    return HttpResponse(st('/gist/gists.html', **tdt))


def make_page_args(request, name, ext=''):
    page = request.GET.get('page', 1)
    start = 5 * (int(page) - 1)
    link_prev = _make_links(name, int(page) - 1, ext=ext)
    link_next = _make_links(name, int(page) + 1, ext=ext)
    sort = request.GET.get('sort', 'created')
    direction = request.GET.get('direction', 'desc')
    return (page, start, link_prev, link_next, sort, direction)


def _make_links(name, page, ext=''):
    if page < 1:
        return ''
    if page and page >= 1:
        if ext:
            return '/gist/%s/%s/?page=%s' % (name, ext, page)
        else:
            return '/gist/%s/?page=%s' % (name, page)
