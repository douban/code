"""vilya URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from views.django import views
from views.django import user
from views.django import gist
from views.django import gist_user
from views.django import gist_raw
from views.django import gist_embed
from views.django import gist_comment


urlpatterns = [
    # user
    url(r'^login/?$', user.login, name='user_login'),
    url(r'^logout/?$', user.logout, name='user_logout'),
    url(r'^register/?$', user.register, name='user_register'),
    url(r'^people/(?P<username>\w+)/praises', user.praises, name='user_praises'),
    url(r'^people/(?P<username>\w+)/followers', user.followers, name='user_followers'),
    url(r'^people/(?P<username>\w+)/following', user.following, name='user_following'),
    url(r'^people/(?P<username>\w+)/badges', user.badges, name='user_badges'),
    url(r'^people/(?P<username>\w+)/contributions', user.contributions, name='user_contributions'),
    url(r'^people/(?P<username>\w+)/contribution_detail', user.contribution_detail, name='user_contribution_detail'),
    url(r'^people/(?P<username>\w+)', user.index, name='user_index'),

    # gist
    url(r'^gist/$', gist.index, name='gist_index'),
    url(r'^gist/discover$', gist.discover, name='gist_discover'),
    url(r'^gist/forked$', gist.forked, name='gist_forked'),
    url(r'^gist/starred$', gist.starred, name='gist_starred'),
    url(r'^gist/(?P<username>\w+)/forked$', gist_user.forked, name='gist_user_forked'),
    url(r'^gist/(?P<username>\w+)/starred$', gist_user.starred, name='gist_user_starred'),
    url(r'^gist/(?P<username>\w+)/?$', gist_user.index, name='gist_user_index'),
    url(r'^gist/(?P<username>\w+)/(?P<id>[0-9]+)/?$', gist_user.gist_index, name='gist_gist_index'),
    url(r'^gist/(?P<username>\w+)/(?P<id>[0-9]+).js$', gist_embed.index, name='gist_embed_index'),
    url(r'^gist/(?P<username>\w+)/(?P<id>[0-9]+)/comments/$', gist_comment.index, name='gist_comment_index'),
    url(r'^gist/(?P<username>\w+)/(?P<id>[0-9]+)/comments/(?P<comment_id>[0-9]+)$', gist_comment.comment, name='gist_comment_comment'),
    url(r'^gist/(?P<username>\w+)/(?P<id>[0-9]+)/revisions/$', gist_user.gist_revisions, name='gist_user_gist_revisions'),
    url(r'^gist/(?P<username>\w+)/(?P<id>[0-9]+)/download$', gist_user.gist_download, name='gist_user_gist_download'),
    url(r'^gist/(?P<username>\w+)/(?P<id>[0-9]+)/edit$', gist_user.gist_edit, name='gist_user_gist_edit'),
    url(r'^gist/(?P<username>\w+)/(?P<id>[0-9]+)/delete$', gist_user.gist_delete, name='gist_user_gist_delete'),
    url(r'^gist/(?P<username>\w+)/(?P<id>[0-9]+)/(?P<revision>\w+)$', gist_user.gist_index, name='gist_gist_index_revision'),
    url(r'^gist/(?P<username>\w+)/(?P<id>[0-9]+)/raw/(?P<revision>\w+)/(?P<filename>.*)$', gist_raw.index, name='gist_raw_index'),

    # misc
    url(r'^mirrors/?$', views.mirrors, name="views_mirrors"),
    url(r'^vilya', views.index),
    url(r'^admin/', admin.site.urls),
]
