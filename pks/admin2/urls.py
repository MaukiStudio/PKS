#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url

from admin2 import views


urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^placed/$', views.placed, name='placed'),
    url(r'^placed/(?P<uplace_id>[0-9A-Za-z]+)\.uplace/$', views.placed_detail, name='placed_detail'),
]
