#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url

from ui import views


urlpatterns = [
    url(r'^confirm_ok/$', views.confirm_ok, name='confirm_ok'),
    url(r'^confirm_fail/$', views.confirm_fail, name='confirm_fail'),
]
