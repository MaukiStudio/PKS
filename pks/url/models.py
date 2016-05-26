#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from re import compile as re_compile
from rest_framework import status

from base.models import Content
from base.legacy.urlnorm import norms as url_norms
from requests import get as requests_get, head as requests_head

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

        # javascript 로 동작해서 body 를 받아야만 하는 단축 URL 처리 : 현재는 네이버 단축 URL 만 확인됨
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

        # URL redirect 처리 : 301 에 의한 URL redirect
        #elif URL_REGEX_4SQUARE_SHORTENER_URL.match(url):
        else:
            headers = {'user-agent': 'Chrome'}
            # 너무 느리니 rediect 쳐서 들어가는 것은 한번만...
            for i in xrange(1):
                r = requests_head(url, headers=headers, allow_redirects=False)
                if r.status_code == status.HTTP_200_OK:
                    url = r.url
                    break
                if r.status_code in (status.HTTP_301_MOVED_PERMANENTLY,):
                    redirect_url = r.headers['location']
                    if not redirect_url.startswith('http'):
                        url = '/'.join(url.split('/')[:3]) + redirect_url
                    else:
                        url = redirect_url

        return url_norms(url)
