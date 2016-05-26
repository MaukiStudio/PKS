#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from re import compile as re_compile
from rest_framework import status

from base.models import Content
from base.legacy.urlnorm import norms as url_norms
from pks.settings import SERVER_HOST
from requests import get as requests_get

URL_REGEX_NAVER_SHORTENER_URL = re_compile(r'^https?://me2\.do/[A-za-z0-9_\-]+$')
URL_REGEX_4SQUARE_SHORTENER_URL = re_compile(r'^https?://4sq\.com/[A-za-z0-9_\-]+$')


class Url(Content):
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

        # 단축 URL 처리
        if URL_REGEX_NAVER_SHORTENER_URL.match(url):
            headers = {'user-agent': 'Chrome'}
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
        elif URL_REGEX_4SQUARE_SHORTENER_URL.match(url):
            headers = {'user-agent': 'Chrome'}
            r = requests_get(url, headers=headers)
            content_type = r.headers.get('content-type')
            if r.status_code in (status.HTTP_200_OK,) and content_type and content_type.startswith('text/html'):
                url = url_norms(r.url)

        return url
