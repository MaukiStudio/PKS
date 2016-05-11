#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from re import compile as re_compile
from rest_framework import status
from urllib2 import unquote

from base.models import Content
from base.legacy.urlnorm import norms as url_norms
from pks.settings import SERVER_HOST
from requests import get as requests_get

URL_REGEX_NAVER_SHORTENER_URL = re_compile(r'^https?://me2\.do/[A-za-z0-9_\-]+$')


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
        url = raw_content.strip()

        # 네이버 단축 URL 처리 편의를 위한 기능
        try:
            pos = url.index('http')
            url = url[pos:].split('\n')[0]
        except ValueError:
            pass

        # URL encoding 처리
        url = unquote(url.encode('utf-8')).decode('utf-8')

        url = url_norms(url)
        if not url.startswith('http'):
            url = '%s%s' % (SERVER_HOST, url)

        # 네이버 단축 URL 처리
        # TODO : 다른 단축 URL 처리 구현과 함께 리팩토링 필요
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
                        url = url_redirected

        return url
