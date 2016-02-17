#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url, include
from django.contrib import admin

from rest_framework.routers import DefaultRouter
from filebrowser.sites import site as fb_site

from account import views


router = DefaultRouter()
router.register(r'vds', views.VDViewset)
router.register(r'user', views.UserViewset)


urlpatterns = [
    url(r'^', include(router.urls)),

    url(r'^admin/filebrowser/', include(fb_site.urls)),
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/', admin.site.urls),
]
