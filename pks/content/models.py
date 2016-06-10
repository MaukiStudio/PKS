#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from uuid import UUID
from re import compile as re_compile
from django.contrib.gis.db import models
from json import loads as json_loads, dumps as json_dumps

from base.models import Content
from phonenumbers import parse, format_number, PhoneNumberFormat
from pyquery import PyQuery
from pathlib2 import Path

FOURSQUARE_CLIENT_ID = 'QEA4FRXVQNHKUQYFZ3IZEU0EI0FDR0MCZL0HEZKW11HUNCTW'
FOURSQUARE_CLIENT_SECRET = '4VU0FLFOORV13ETKHN5UNYKGBNPZBAJ3OGGKC5E2NILYA2VD'


LP_REGEXS = (
    # '4ccffc63f6378cfaace1b1d6.4square'
    (re_compile(r'^(?P<PlaceId>[a-z0-9]+)\.4square$'), '4square'),

    # '21149144.naver'
    (re_compile(r'^(?P<PlaceId>[0-9]+)\.naver$'), 'naver'),

    # '14720610.kakao'
    (re_compile(r'^(?P<PlaceId>[0-9]+)\.kakao$'), 'kakao'),

    # 'ChIJrTLr-GyuEmsRBfy61i59si0.google'
    (re_compile(r'^(?P<PlaceId>[A-za-z0-9_\-]+)\.google$'), 'google'),
)
LP_REGEXS_URL = (
    # 'http://map.naver.com/local/siteview.nhn?code=21149144'
    # 'http://m.map.naver.com/siteview.nhn?code=31176899'
    (re_compile(r'^https?://.*map\.naver\.com/.*\?code=(?P<PlaceId>[0-9]+)&?.*$'), 'naver'),

    # 'http://map.naver.com/?app=Y&version=10&appMenu=location&pinId=31130096&pinType=site&lat=37.3916387&lng=127.0584149&title=능이향기&dlevel=11'
    # 'https://m.map.naver.com/viewer/map.nhn?pinType=site&pinId=21652462'
    (re_compile(r'^https?://.*map\.naver\.com/.*\?.*pinId=(?P<PlaceId>[0-9]+)&?.*$'), 'naver'),

    # 'http://m.store.naver.com/restaurants/detail?id=37333252'
    (re_compile(r'^https?://m\.store\.naver\.com/[A-za-z0-9_\-]+/detail\?id=(?P<PlaceId>[0-9]+)&?.*$'), 'naver'),


    # 'https://place.kakao.com/places/14720610/홍콩'
    (re_compile(r'^https?://place\.kakao\.com/places/(?P<PlaceId>[0-9]+)&?.*$'), 'kakao'),

    # 'http://m.map.daum.net/actions/detailInfoView?id=15493954'
    (re_compile(r'^https?://(m\.)?map\.daum\.net/actions/detailInfoView\?id=(?P<PlaceId>[0-9]+)&?.*$'), 'kakao'),

    # 'https://foursquare.com/v/방아깐/4ccffc63f6378cfaace1b1d6'
    (re_compile(r'^https?://.*foursquare\.com/v/.+/(?P<PlaceId>[a-z0-9]+)&?.*$'), '4square'),

    # 'http://foursquare.com/v/4ccffc63f6378cfaace1b1d6'
    (re_compile(r'^https?://.*foursquare\.com/v/(?P<PlaceId>[a-z0-9]+)&?.*$'), '4square'),
)

LP_TYPE = {'4square': 1, 'naver': 2, 'google': 3, 'kakao': 4,}


class LegacyPlace(Content):
    place = models.ForeignKey('place.Place', on_delete=models.SET_DEFAULT, null=True, default=None, related_name='lps')
    lp_type = models.SmallIntegerField(blank=True, null=True, default=None)

    class Meta:
        unique_together = ('place', 'lp_type',)

    # MUST override
    @property
    def contentType(self):
        splits = self.content.split('.')
        return splits[1]

    @property
    def accessedType(self):
        splits = self.content.split('.')
        if splits[1] in ('4square', 'google'):
            return 'json'
        else:
            return 'html'

    @property
    def summarizedType(self):
        return 'json'

    @classmethod
    def normalize_content(self, raw_content):
        for regex in LP_REGEXS+LP_REGEXS_URL:
            searcher = regex[0].search(raw_content)
            if searcher:
                return '%s.%s' % (searcher.group('PlaceId'), regex[1])

    @property
    def _id(self):
        splits = self.content.split('.')
        if splits[1] == 'google':
            h = self.get_md5_hash(splits[0])
            h0 = hex(int(h[0], 16) | 8)[2:]
            return UUID('%s%s' % (h0, h[1:]))
        else:
            return UUID(b'0000000%d%s' % (LP_TYPE[self.contentType], splits[0].rjust(24, b'0')),)

    @property
    def url_for_access(self):
        splits = self.content.split('.')
        if splits[1] == 'naver':
            return 'http://map.naver.com/local/siteview.nhn?code=%s' % splits[0]
        elif splits[1] == 'kakao':
            return 'http://place.kakao.com/places/%s/' % splits[0]
        elif splits[1] == '4square':
            #return 'https://foursquare.com/v/%s' % splits[0]
            return '4square://%s' % splits[0]
        else:
            # TODO : 구글도 땡겨올 수 있게끔 수정
            raise NotImplementedError

    def access_force(self, timeout=3):
        url = self.url_for_access
        if url.startswith('http'):
            super(LegacyPlace, self).access_force(timeout=timeout)
            return

        result = None
        if url.startswith('4square'):
            from foursquare import Foursquare
            client = Foursquare(client_id=FOURSQUARE_CLIENT_ID, client_secret=FOURSQUARE_CLIENT_SECRET)
            result = json_dumps(client.venues(url.split('//')[1]), ensure_ascii=False)
        else:
            raise NotImplementedError

        if result:
            file = Path(self.path_accessed)
            if not file.parent.exists():
                file.parent.mkdir(parents=True)
            summary = Path(self.path_summarized)
            if not Path(self.path_summarized).parent.exists():
                summary.parent.mkdir(parents=True)
            file.write_text(result)
            self._cache_accessed = result.replace('\r', '')

    @classmethod
    def get_from_url(cls, url):
        for regex in LP_REGEXS_URL:
            searcher = regex[0].search(url.content)
            if searcher:
                PlaceId = searcher.group('PlaceId')
                json = '{"content": "%s.%s"}' % (PlaceId, regex[1])
                return cls.get_from_json(json)
        return None


    def summarize_force(self, accessed=None):
        # TODO : 각종 URL 패턴들에 대해 정보 수집하여 요약
        if not accessed:
            accessed = self.content_accessed

        if accessed:
            if self.contentType == 'naver':
                self.summarize_force_naver(accessed)
            elif self.contentType == 'kakao':
                self.summarize_force_kakao(accessed)
            elif self.contentType == '4square':
                self.summarize_force_4square(accessed)
            else:
                raise NotImplementedError

    def summarize_force_naver(self, accessed):
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
        img_url = pq('meta[property="og:image"]').attr('content')

        # TODO : Post class 를 이용하여 리팩토링
        json = '''
            {
                "lonLat": {"lon": %f, "lat": %f},
                "name": {"content": "%s"},
                "phone": {"content": "%s"},
                "addr1": {"content": "%s"},
                "addr2": {"content": "%s"},
                "images": [{"content": "%s"}],
                "lps": [{"content": "%s"}]
            }
        ''' % (lon, lat, name, phone, addr_new, addr, img_url, self.content,)

        f = Path(self.path_summarized)
        f.write_text(json)

    def summarize_force_kakao(self, accessed):
        # 파싱
        pq = PyQuery(accessed)
        str1 = pq('div').attr('data-react-props')
        str2 = str1
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
        img_url = pq('meta[property="og:image"]').attr('content')

        # TODO : Post class 를 이용하여 리팩토링
        json = '''
            {
                "lonLat": {"lon": %f, "lat": %f},
                "name": {"content": "%s"},
                "phone": {"content": "%s"},
                "addr1": {"content": "%s"},
                "addr2": {"content": "%s"},
                "images": [{"content": "%s"}],
                "lps": [{"content": "%s"}]
            }
        ''' % (lon, lat, name, phone, addr_new, addr, img_url, self.content,)

        f = Path(self.path_summarized)
        f.write_text(json)

    def summarize_force_4square(self, accessed):
        # 파싱
        d = json_loads(accessed)['venue']

        # 주요 정보
        lon = float(d['location']['lng'])
        lat = float(d['location']['lat'])
        name = d['name']
        phone = d['contact']['phone']
        if phone:
            phone = PhoneNumber.normalize_content(phone)
        addr_new = d['location']['formattedAddress'][0]
        bp = d['bestPhoto']
        img_url = '%s%dx%d%s' % (bp['prefix'], bp['width'], bp['height'], bp['suffix'])

        # TODO : Post class 를 이용하여 리팩토링
        json = '''
            {
                "lonLat": {"lon": %f, "lat": %f},
                "name": {"content": "%s"},
                "phone": {"content": "%s"},
                "addr1": {"content": "%s"},
                "images": [{"content": "%s"}],
                "lps": [{"content": "%s"}]
            }
        ''' % (lon, lat, name, phone, addr_new, img_url, self.content,)

        f = Path(self.path_summarized)
        f.write_text(json)

    def pre_save(self):
        if self.is_accessed:
            self.summarize()
        self.lp_type = LP_TYPE[self.contentType]

    @property
    def content_summarized(self):
        from place.post import PostBase
        file = Path(self.path_summarized)
        json_str = file.read_text()
        return PostBase(json_str)


class PhoneNumber(Content):

    # MUST override
    @property
    def contentType(self):
        return 'phone'

    @property
    def accessedType(self):
        return 'txt'


    # CAN override
    @classmethod
    def normalize_content(cls, raw_content):
        # TODO : 국가 관련 처리 개선
        p = parse(raw_content, 'KR')
        r = format_number(p, PhoneNumberFormat.E164)
        return r

    @property
    def _id(self):
        return UUID(self.content[1:].rjust(32, b'0'))

    @property
    def url_for_access(self):
        # 구글 검색 땡겨올 수 있도록 수정
        raise NotImplementedError
        # TODO : 국가 처리
        p = parse(self.content, 'KR')
        r = format_number(p, PhoneNumberFormat.NATIONAL)
        return 'http://www.google.com/#q="%s"' % r


class PlaceName(Content):
    # MUST override
    @property
    def contentType(self):
        return 'pname'

    @property
    def accessedType(self):
        return 'html'


class Address(Content):
    # MUST override
    @property
    def contentType(self):
        return 'addr'

    @property
    def accessedType(self):
        return 'html'


class PlaceNote(Content):
    # MUST override
    @property
    def contentType(self):
        return 'pnote'

    @property
    def accessedType(self):
        return 'html'

    @property
    def content_for_search(self):
        return self.content.replace('#', '')

    # 관련 test 는 tag/test_models.py 에
    def process_tag_realtime(self):
        from tag.models import Tag, PlaceNoteTag
        for str in self.content.split(' '):
            if str.startswith('#'):
                for rawTagName in str.split('#'):
                    if rawTagName:
                        tag, is_created = Tag.get_or_create_smart(rawTagName)
                        PlaceNoteTag.objects.get_or_create(tag=tag, placeNote=self)

    @classmethod
    def get_or_create_smart(cls, raw_content):
        instance, is_created = super(PlaceNote, cls).get_or_create_smart(raw_content)
        instance.process_tag_realtime()
        return instance, is_created


class ImageNote(Content):
    # MUST override
    @property
    def contentType(self):
        return 'inote'

    @property
    def accessedType(self):
        return 'html'


class TagName(Content):
    # MUST override
    @property
    def contentType(self):
        return 'tname'

    @property
    def accessedType(self):
        return 'html'
