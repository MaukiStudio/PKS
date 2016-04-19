#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url

from admin2 import views


urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^mapping/$', views.mapping, name='mapping'),
    url(r'^mapping/(?P<uplace_id>[0-9A-Za-z]+)\.uplace/$', views.mapping_detail, name='mapping_detail'),
]
