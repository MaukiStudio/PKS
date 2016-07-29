#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from re import compile as re_compile
from rest_framework import status
from django.contrib.gis.db import models

from base.models import Content
from base.legacy.urlnorm import norms as url_norms
from requests import get as requests_get
from place.models import Place, PostPiece

URL_REGEX_NAVER_SHORTENER_URLS = [
    re_compile(r'^https?://me2\.do/[A-za-z0-9_\-]+$'),
    re_compile(r'^https?://naver\.me/[A-za-z0-9_\-]+$'),
]
URL_REGEX_4SQUARE_SHORTENER_URL = re_compile(r'^https?://4sq\.com/[A-za-z0-9_\-]+$')


class Url(Content):

    places = models.ManyToManyField(Place, through='UrlPlaceRelation', related_name='urls')

    # MUST override
    @property
    def contentType(self):
        return 'url'

    @property
    def accessedType(self):
        return 'html'

    # CAN override
    @classmethod
    def normalize_content(cls, raw_content):
        url = url_norms(raw_content)

        # javascript 로 동작해서 body 를 받아야만 하는 단축 URL 처리 : 현재는 네이버 단축 URL 만 확인됨
        if URL_REGEX_NAVER_SHORTENER_URLS[0].match(url) or URL_REGEX_NAVER_SHORTENER_URLS[1].match(url):
            headers = {'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.82 Safari/537.36'}
            r = requests_get(url, headers=headers)
            content_type = r.headers.get('content-type')
            if r.status_code in (status.HTTP_200_OK,) and content_type and content_type.startswith('text/html'):
                str = r.content
                if str.startswith(b'<script>window.location.replace("'):
                    pos1 = str.index('"') + 1
                    pos2 = str.index('"', pos1)
                    if pos1 < pos2:
                        url_redirected = str[pos1:pos2]
                        url = url_norms(url_redirected)

        # URL redirect 처리 : 301 에 의한 URL redirect : 현재는 포스퀘어 단축 URL 만 처리
        elif URL_REGEX_4SQUARE_SHORTENER_URL.match(url):
            headers = {'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.82 Safari/537.36'}
            r = requests_get(url, headers=headers)
            content_type = r.headers.get('content-type')
            if r.status_code in (status.HTTP_200_OK,) and content_type and content_type.startswith('text/html'):
                url_redirected = r.url
                url = url_norms(url_redirected)

        return url

    def add_place(self, place):
        upr, is_created = UrlPlaceRelation.objects.get_or_create(url=self, place=place)
        if is_created:
            pps = PostPiece.objects.filter(data__urls__contains=[self.ujson])
            for pp in pps:
                uplace = pp.uplace
                uplace.process_child(place)
        return upr

    # TODO : add_place() 에 의해 생성된 UserPlace 에 대해, remove_place() 가 호출되면 어떻게 처리하는 것이 좋을지 고민 후 구현
    def remove_place(self, place):
        upr = UrlPlaceRelation.objects.get(url=self, place=place)
        upr.delete()


class UrlPlaceRelation(models.Model):
    url = models.ForeignKey(Url, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='+')
    place = models.ForeignKey(Place, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='+')

    class Meta:
        unique_together = ('url', 'place',)
