#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from base.models import Content
from base.legacy.urlnorm import norms as url_norms
from pks.settings import SERVER_HOST
from content.models import LP_REGEXS_URL, PhoneNumber
from pyquery import PyQuery
from json import loads as json_loads
from pathlib2 import Path


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
        url = url_norms(raw_content.strip())
        if not url.startswith('http'):
            url = '%s%s' % (SERVER_HOST, url)
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
                    "addrs": [
                        {"content": "%s"},
                        {"content": "%s"}
                    ],
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
