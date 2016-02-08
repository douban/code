# -*- coding: utf-8 -*-

from django.http import HttpResponse
from django.http import JsonResponse
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from vilya.libs.template import st

FOLLOW_LIST_USER_COUNT = 24


def index(request, username):
    from vilya.models.feed import get_user_feed
    from vilya.models.project import CodeDoubanProject
    from vilya.models.user import User
    name = username
    # TODO(xutao) validate username
    quixote_user = User(username)
    django_user = request.user
    user = quixote_user

    # FIXME(xutao) translate current django user to quixote user
    request.user = user

    your_projects = CodeDoubanProject.get_projects(owner=name,
                                                   sortby='lru')
    actions = get_user_feed(name).get_actions(0, 20)
    followers_count = user.followers_count
    following_count = user.following_count
    return HttpResponse(st('people.html', **locals()))


@csrf_exempt
def login(request):
    from django.contrib.auth import authenticate, login
    from vilya.models.user import User
    from vilya.models.user import set_user

    if request.method == 'POST':
        name = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=name, password=password)
        if user is not None:
            continue_url = request.GET.get('continue', '') \
                or request.META.get('Referer', '')

            # django user
            login(request, user)

            # quixote user
            request.user = User(user.username)
            set_user(user.id)
            return JsonResponse({"r": 0, "continue": continue_url or "/"})
        else:
            message = '用户名或密码错误！'
            return JsonResponse({"r": 1, 'message': message})
    return HttpResponse(st('login.html'))


@csrf_exempt
def register(request):
    from vilya.models.nuser import User2
    from vilya.models.user import set_user
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        if not email:
            return JsonResponse({'r': 1, 'message': 'Email没有指定'})

        user_name = email.split('@')[0]
        if User2.is_exists(user_name):
            return JsonResponse({'r': 1, 'message': '用户已存在'})

        # django user
        # FIXME(xutao) get user name from user input
        user = User.objects.create_user(user_name, email, password)
        user.save()

        # quixote user
        code_user = User2.add(user_name, password)
        set_user(code_user.id)
        return JsonResponse({'r': 0})
    return HttpResponse(st('register.html'))


@csrf_exempt
def logout(request):
    from django.contrib.auth import logout
    from vilya.models.user import User

    if request.method == 'POST':
        logout(request)
        continue_url = request.GET.get('continue', '') or request.META.get('Referer', '')
        return HttpResponseRedirect(continue_url or '/')

    if request.user:
        user = User(request.user.username)
        context = {}
        context['current_user'] = user
    return HttpResponse(st('logout.html', **context))


def badges(request, username):
    import itertools
    from datetime import datetime, timedelta
    from vilya.models.badge import Badge
    name = username
    badge_items = Badge.get_badge_items()
    _date_badge_items = [i for i in badge_items if i.date]
    items_groupby_date = itertools.groupby(
        _date_badge_items, lambda badge_item: badge_item.date.date())
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    return HttpResponse(st('badge/timeline.html', **locals()))


def follow(request, username):
    # FIXME(xutao)
    action = 1
    msg = "success"
    return JsonResponse({"action": action, "msg": msg})


def unfollow(request, username):
    # FIXME(xutao)
    action = -1
    msg = "success"
    return JsonResponse({"action": action, "msg": msg})


def following(request, username):
    from vilya.models.user import User
    name = username
    list_type = "following"
    user_list = User(name).get_following()
    return HttpResponse(follow_list(request, list_type, user_list))


def followers(request, username):
    from vilya.models.user import User
    name = username
    list_type = "followers"
    user_list = User(name).get_followers()
    return HttpResponse(follow_list(request, list_type, user_list))


def add_rec(request):
    # TODO(xutao)
    return HttpResponse(st('people_add_rec.html', **locals()))


def praises(request, username):
    from vilya.models.recommendation import Recommendation
    name = username
    recs = Recommendation.gets_by_user(name)
    return HttpResponse(st('people_recs.html', **locals()))


def contributions(request, username):
    import time
    from datetime import datetime
    from vilya.models.contributions import UserContributions
    name = username
    res = {}
    for date_, contribution in UserContributions.get_by_user(
            name).iteritems():
        timestamp = time.mktime(
            datetime.strptime(date_, '%Y-%m-%d').timetuple())
        score = contribution[0]
        res.setdefault(timestamp, score)
    return JsonResponse(res)


def contribution_detail(request, username):
    from vilya.models.contributions import UserContributions
    from vilya.models.ticket import Ticket
    import dateutil.parser
    name = username
    req_date = request.GET.get('date')
    if req_date:
        try:
            req_date = dateutil.parser.parse(
                req_date).astimezone(dateutil.tz.tzoffset('EST', 8*3600))
        except ValueError as e:
            return ""
        contributions = UserContributions.get_by_date(name, req_date)
        owned = contributions.get('owned_tickets')
        commented = contributions.get('commented_tickets')
        owned_tickets = filter(None, [Ticket.get(id_) for id_ in owned])
        commented_tickets = filter(None, [Ticket.get(comment[0])
                                            for comment in commented])
        return HttpResponse(st('people_contribution_detail.html', **locals()))
    return HttpResponse("")


def follow_list(name, request, list_type, user_list):
    page = int(request.get_form_var('page', 1))
    count = len(user_list)
    start = FOLLOW_LIST_USER_COUNT * (page - 1)
    n_pages = count / FOLLOW_LIST_USER_COUNT + 1
    user_list = user_list[start:(start + FOLLOW_LIST_USER_COUNT)]
    current_user = user = request.user
    current_user_following = current_user.get_following() \
                                if current_user else []
    return st('follow-list.html', **locals())
