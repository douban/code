# -*- coding: utf-8 -*-

from django.http import HttpResponse
from django.http import Http404
from django.http import HttpResponseRedirect
from django.http import HttpResponseForbidden
from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from vilya.libs.template import st
from vilya.views.django.gist import make_page_args, _make_links, _get_req_gist_data


def index(request, username):
    from vilya.models.gist import Gist
    return _render(username, request, Gist.gets_by_owner)


def forked(request, username):
    from vilya.models.gist import Gist
    return _render(username, request, Gist.forks_by_user)


def starred(request, username):
    from vilya.models.gist import Gist
    return _render(username, request, Gist.stars_by_user)


def public(request, username):
    from vilya.models.gist import Gist
    return _render(username, request, Gist.publics_by_user)


def secret(request, username):
    from vilya.models.gist import Gist
    current_user = request.user
    if not current_user or current_user.username != username:
        return HttpResponseRedirect('/gist/%s' % username)
    return _render(username, request, Gist.secrets_by_user)


def _render(username, request, func):
    from vilya.views.util import is_mobile_device
    from vilya.models.user import User
    from vilya.models.gist import Gist
    name = username

    # FIXME(xutao) check user
    user = User(name)

    current_user = request.user
    is_self = current_user and current_user.username == name
    ext = request.get_path().split('/')[-1]
    (page, start, link_prev, link_next, sort, direction) =\
        make_page_args(request, name, ext=ext)
    n_all = Gist.count_user_all(name, is_self)
    n_fork = Gist.count_user_fork(name)
    n_star = Gist.count_user_star(name)

    if sort not in ('created', 'updated') \
            or direction not in ('desc', 'asc'):
        raise Http404()

    gists = func(name, start=start, limit=5, sort=sort, direction=direction)

    tdt = {
        'request': request,
        'gists': gists,
        'user': user,
        'page': int(page),
        'link_prev': link_prev,
        'link_next': link_next,
        'n_all': n_all,
        'n_fork': n_fork,
        'n_star': n_star,
        'sort': sort,
        'direction': direction
    }
    if is_mobile_device(request):
        return HttpResponse(st('/m/gist/user_gists.html', **tdt))
    return HttpResponse(st('/gist/user_gists.html', **tdt))


def gist_index(request, username, id, revision=None):
    from vilya.models.gist import Gist
    from vilya.views.util import is_mobile_device

    gist = Gist.get(id)
    user = request.user
    if revision and gist.repo.is_commit(revision):
        tdt = {'request': request,
               'gist': gist,
               'ref': revision,
               'user': user}
        return HttpResponse(st('/gist/gist_detail.html', **tdt))
    tdt = dict(request=request, gist=gist, ref='master', user=user)
    if is_mobile_device(request):
        return HttpResponse(st('/m/gist/gist_detail.html', **tdt))
    return HttpResponse(st('/gist/gist_detail.html', **tdt))


def gist_revisions(request, username, id):
    from vilya.models.gist import Gist

    user = request.user

    gist = Gist.get(id)
    page = int(request.GET.get('page', 1))
    skip = 3 * (page - 1)
    revlist = gist.get_revlist_with_renames(max_count=3, skip=skip)
    link_prev = _make_links(id, int(page) - 1, ext="revisions")
    if revlist:
        link_next = _make_links(id, int(page) + 1, ext="revisions")
    else:
        link_next = ''
    content = []
    for r in revlist:
        # FIXME: try-except ?
        content.append(gist.repo.get_diff(r.sha, rename_detection=True))
    tdt = {
        'request': request,
        'gist': gist,
        'content': content,
        'revlist': revlist,
        'link_prev': link_prev,
        'link_next': link_next,
        'user': user,
        'current_user': user,
    }
    return HttpResponse(st('/gist/gist_revisions.html', **tdt))


def gist_forks(request, username, id):
    from vilya.models.gist import Gist
    user = request.user
    gist = Gist.get(id)
    tdt = dict(request=request, gist=gist, user=user)
    return HttpResponse(st('/gist/gist_forks.html', **tdt))


def gist_stars(request, username, id):
    from vilya.models.gist import Gist
    user = request.user
    gist = Gist.get(id)
    tdt = dict(request=request, gist=gist, user=user)
    return HttpResponse(st('/gist/gist_stars.html', **tdt))


def gist_fork(request, username, id):
    from vilya.models.gist import Gist
    user = request.user
    gist = Gist.get(id)
    new_gist = gist.fork(user.username)
    return HttpResponseRedirect(new_gist.url)


def gist_unstar(request, username, id):
    from vilya.models.gist import Gist
    from vilya.models.gist_star import GistStar
    user = request.user
    gist = Gist.get(id)
    star = GistStar.get_by_gist_and_user(id, user.username)
    if star:
        star.delete()
    return HttpResponseRedirect(gist.url)


def gist_star(request, username, id):
    from vilya.models.gist import Gist
    from vilya.models.gist_star import GistStar
    user = request.user
    gist = Gist.get(id)
    GistStar.add(id, user.username)
    return HttpResponseRedirect(gist.url)


@csrf_exempt
def gist_edit(request, username, id):
    from vilya.views.util import is_mobile_device
    from vilya.models.gist import Gist
    user = request.user
    gist = Gist.get(id)
    if not user or user.username != gist.owner_id:
        raise HttpResponseForbidden()

    if request.method == 'POST':
        desc, is_public, names, contents, oids = _get_req_gist_data(
            request)
        gist.update(desc, names, contents, oids)
        return HttpResponseRedirect(gist.url)

    tdt = dict(request=request, gist=gist, user=user)
    if is_mobile_device(request):
        return HttpResponse(st('/m/gist/edit.html', **tdt))
    return HttpResponse(st('/gist/edit.html', **tdt))


def gist_delete(request, username, id):
    from vilya.models.gist import Gist
    user = request.user
    gist = Gist.get(id)
    if not user or user.username != gist.owner_id:
        raise HttpResponseForbidden()
    gist.delete()
    return HttpResponseRedirect('/gist/%s' % user.username)


def gist_download(request, username, id):
    from vilya.models.gist import Gist
    gist = Gist.get(id)
    response = StreamingHttpResponse(content_type='application/x-gzip')
    response['Content-Disposition'] = 'filename=code_gist_%s.tar.gz' % id
    response.streaming_content = gist.repo.archive(name="code_gist_%s" % id)
    return response


def gist_re_index(request, username, id):
    # TODO(xutao) remove es support
    from vilya.models.gist import Gist
    gist = Gist.get(id)
    return HttpResponseRedirect(gist.url)
