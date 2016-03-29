#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url, include
from django.contrib import admin

from rest_framework.routers import DefaultRouter
from filebrowser.sites import site as fb_site

from account import views as account_views
from image import views as image_views
from url import views as url_views
from place import views as place_views


router = DefaultRouter()
router.register(r'vds', account_views.VDViewset)
router.register(r'users', account_views.UserViewset)
router.register(r'rus', account_views.RealUserViewset)
router.register(r'imgs', image_views.ImageViewset)
router.register(r'urls', url_views.UrlViewset)
router.register(r'places', place_views.PlaceViewset)


urlpatterns = [
    url(r'^', include(router.urls)),

    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    url(r'^admin/filebrowser/', include(fb_site.urls)),
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/', admin.site.urls),
]
