#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url

from ui import views


urlpatterns = [
    # 장소 태깅 서비스
    url(r'^diaries/$', views.diaries, name='diaries'),
    url(r'^diaries/init', views.init, name='init'),
    url(r'^diaries/register_email', views.register_email, name='register_email'),
    url(r'^diaries/(?P<uplace_id>[0-9A-Za-z]+)\.uplace/paste/$', views.paste, name='paste'),
    url(r'^diaries/(?P<uplace_id>[0-9A-Za-z]+)\.uplace/temp/$', views.temp, name='temp'),
    url(r'^diaries/(?P<uplace_id>[0-9A-Za-z]+)\.uplace/make_shorten_url/$', views.make_shorten_url, name='make_shorten_url'),
    url(r'^diaries/(?P<enc_uplace_id>[0-9A-Za-z-_]+)/$', views.detail, name='detail'),

    # 이메일 인증
    url(r'^confirm_ok/$', views.confirm_ok, name='confirm_ok'),
    url(r'^confirm_fail/$', views.confirm_fail, name='confirm_fail'),
]
