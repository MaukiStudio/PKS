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
        # TODO : 각종 URL 패턴들에 대해 정보 수집하여 요약
        if not accessed:
            accessed = self.content_accessed

        # TODO : 포스퀘어쪽 처리되고 나면 하기의 [:-2] 는 뺀다
        regexs = LP_REGEXS_URL[:-2]
        for regex in regexs:
            searcher = regex[0].search(self.content)
            if searcher:
                lp_PlaceId = searcher.group('PlaceId')
                if regex[1] == 'naver':
                    self.summarize_force_naver(accessed, lp_PlaceId)
                elif regex[1] == 'kakao':
                    self.summarize_force_kakao(accessed, lp_PlaceId)
                else:
                    raise NotImplementedError

    def summarize_force_naver(self, accessed, lp_PlaceId):
        lp_content = '%s.naver' % lp_PlaceId

        # 파싱
        # TODO : 안전하게 파싱하여 처리. 라이브러리 알아볼 것
        pq = PyQuery(accessed)
        str1 = pq('script')[4].text
        pos1 = str1.index('siteview')
        pos1 = str1.index('{', pos1)

        pos2 = str1.index('\n', pos1)
        str2 = str1[pos1:pos2-1]
        d0 = json_loads(str2)
        d = d0['summary']

        # 주요 정보
        lon = float(d['coordinate']['x'])
        lat = float(d['coordinate']['y'])
        name = d['name']
        phone = d['phone']
        if phone:
            phone = PhoneNumber.normalize_content(phone)
        addr_new = d['roadAddr']['text']
        addr = d['address']

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

    def summarize_force_kakao(self, accessed, lp_PlaceId):
        lp_content = '%s.kakao' % lp_PlaceId

        # 파싱
        pq = PyQuery(accessed)
        str1 = pq('div').attr('data-react-props')
        str2 = str1[:]
        d0 = json_loads(str2)
        d = d0['result']['place']

        # 주요 정보
        lon = float(d['lng'])
        lat = float(d['lat'])
        name = d['name']
        phone = d['phone']
        if phone:
            phone = PhoneNumber.normalize_content(phone)
        addr_new = d['address']
        addr = d['address_old']

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
            self.summarize()

    @property
    def content_summarized(self):
        from place.post import PostBase
        file = Path(self.path_summarized)
        json_str = file.read_text()
        return PostBase(json_str)
