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


urlpatterns = [
    url(r'^people/(?P<username>\w+)/praises', user.praises, name='user_praises'),
    url(r'^people/(?P<username>\w+)/followers', user.followers, name='user_followers'),
    url(r'^people/(?P<username>\w+)/following', user.following, name='user_following'),
    url(r'^people/(?P<username>\w+)/badges', user.badges, name='user_badges'),
    url(r'^people/(?P<username>\w+)/contributions', user.contributions, name='user_contributions'),
    url(r'^people/(?P<username>\w+)/contribution_detail', user.contribution_detail, name='user_contribution_detail'),
    url(r'^people/(?P<username>\w+)', user.index, name='user_index'),
    url(r'^vilya', views.index),
    url(r'^admin/', admin.site.urls),
]
