#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from re import compile as re_compile
from rest_framework import status

from base.models import Content
from base.legacy.urlnorm import norms as url_norms
from pks.settings import SERVER_HOST
from content.models import LP_REGEXS_URL, PhoneNumber
from pyquery import PyQuery
from json import loads as json_loads
from pathlib2 import Path
from requests import get as requests_get

URL_REGEX_NAVER_SHORTENER_URL = re_compile(r'^http://me2\.do/[A-za-z0-9_\-]+$')
URL_REGEX_NAVER_MAP_URL = re_compile(r'^http://map\.naver\.com/\?.*pinId=(?P<PlaceId>[0-9]+).*$')


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
            url = url[pos:].split('\r')[0]
        except ValueError:
            pass

        url = url_norms(url)
        if not url.startswith('http'):
            url = '%s%s' % (SERVER_HOST, url)

        # 네이버 단축 URL 처리
        # TODO : 구조의 대대적 개선 필요
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
                        searcher = URL_REGEX_NAVER_MAP_URL.search(url_redirected)
                        if searcher:
                            url = 'http://map.naver.com/local/siteview.nhn?code=%s' % searcher.group('PlaceId')

        return url

    def summarize_force(self, accessed=None):
        if not accessed:
            accessed = self.path_accessed

        # TODO : 각종 URL 패턴들에 대해 정보 수집하여 요약

        # 장소화 어드민을 위한 Naver 장소 URL 처리 : 일단 하기 패턴만 처리
        # 'http://map.naver.com/local/siteview.nhn?code=21149144'
        # TODO : Logic 이 엄청 많아지게 됨. 별도의 Class 로 빼는 리팩토링 필요
        regex = LP_REGEXS_URL[0][0]
        searcher = regex.search(self.content)
        if searcher:
            lp_content = '%s.naver' % searcher.group('PlaceId')

            # 파싱
            # TODO : 안전하게 파싱하여 처리. 라이브러리 알아볼 것
            pq = PyQuery(filename=accessed)
            str1 = pq('script')[4].text
            pos1 = str1.index('siteview')
            pos1 = str1.index('{', pos1)
            pos2 = str1.index('\r\n', pos1)
            str2 = str1[pos1:pos2-1]
            d = json_loads(str2)

            # 주요 정보
            lon = float(d['summary']['coordinate']['x'])
            lat = float(d['summary']['coordinate']['y'])
            name = d['summary']['name']
            phone = d['summary']['phone']
            if phone:
                phone = PhoneNumber.normalize_content(phone)
            addr_new = d['summary']['roadAddr']['text']
            addr = d['summary']['address']

            # TODO : Post class 를 이용하여 리팩토링
            json = '''
                {
                    "urls": [{"content": "%s"}],
                    "lonLat": {"lon": %f, "lat": %f},
                    "name": {"content": "%s"},
                    "phone": {"content": "%s"},
                    "addr1": {"content": "%s"},
                    "addr2": {"content": "%s"},
                    "lps": [{"content": "%s"}]
                }
            ''' % (self.content, lon, lat, name, phone, addr_new, addr, lp_content,)

            f = Path(self.path_summarized)
            f.write_text(json)

    def pre_save(self):
        if self.is_accessed:
            self.summarize(self.path_accessed)

    @property
    def content_summarized(self):
        from place.post import PostBase
        file = Path(self.path_summarized)
        json_str = file.read_text()
        return PostBase(json_str)

    @property
    def content_accessed(self):
        file = Path(self.path_accessed)
        return file.read_text()
