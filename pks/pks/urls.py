#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf.urls import url, include
from django.contrib import admin

from rest_framework.routers import DefaultRouter
from filebrowser.sites import site as fb_site
from django.conf import settings
from django.conf.urls.static import static
from account import views as account_views
from image import views as image_views
from url import views as url_views
from place import views as place_views
from content import views as content_views
from importer import views as importer_views
from tag import views as tag_views


router = DefaultRouter()
router.register(r'vds', account_views.VDViewset)
router.register(r'users', account_views.UserViewset)
router.register(r'rus', account_views.RealUserViewset)
router.register(r'storages', account_views.StorageViewset)
router.register(r'trackings', account_views.TrackingViewset)

router.register(r'rfs', image_views.RawFileViewset)
router.register(r'imgs', image_views.ImageViewset)
router.register(r'urls', url_views.UrlViewset)
router.register(r'lps', content_views.LegacyPlaceViewset)
router.register(r'phones', content_views.PhoneNumberViewset)
router.register(r'pnames', content_views.PlaceNameViewset)
router.register(r'addrs', content_views.AddressViewset)
router.register(r'pnotes', content_views.PlaceNoteViewset)
router.register(r'inotes', content_views.ImageNoteViewset)

router.register(r'places', place_views.PlaceViewset)
router.register(r'pps', place_views.PostPieceViewset)
router.register(r'uplaces', place_views.UserPlaceViewset)
router.register(r'proxies', importer_views.ProxyViewset)
router.register(r'importers', importer_views.ImporterViewset)
router.register(r'iplaces', importer_views.ImportedPlaceViewset)

router.register(r'tags', tag_views.TagViewset)
router.register(r'uptags', tag_views.UserPlaceTagViewset)
router.register(r'ptags', tag_views.PlaceTagViewset)


def redirect_to_google_shortener(request, key):
    from django.shortcuts import redirect
    return redirect('http://goo.gl/%s' % key)


urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^g/(?P<key>.+)', redirect_to_google_shortener, name='diaries'),

    url(r'^admin2/', include('admin2.urls', namespace='admin2')),
    url(r'^ui/', include('ui.urls', namespace='ui')),

    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^admin/filebrowser/', include(fb_site.urls)),
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/', admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
