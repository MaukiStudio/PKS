#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url, include
from django.contrib import admin

from rest_framework.routers import DefaultRouter

from account import views


router = DefaultRouter()
router.register(r'vds', views.VirtualDeviceViewset)


urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^admin/', admin.site.urls),
]
