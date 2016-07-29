#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url

from ui import views


urlpatterns = [
    # 장소 태깅 서비스
    url(r'^list/$', views.ui_list, name='list'),

    # 이메일 인증
    url(r'^confirm_ok/$', views.confirm_ok, name='confirm_ok'),
    url(r'^confirm_fail/$', views.confirm_fail, name='confirm_fail'),
]
