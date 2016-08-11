#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from uuid import UUID
from re import compile as re_compile
from django.contrib.gis.db import models
from json import loads as json_loads, dumps as json_dumps
from rest_framework import status
from requests import get as requests_get

from base.models import Content
from phonenumbers import parse, format_number, PhoneNumberFormat
from pyquery import PyQuery
from pathlib2 import Path
from base.google import get_api_key

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

    # 'f-YvkBx8IemC.mango'
    (re_compile(r'^(?P<PlaceId>[A-za-z0-9_\-]+)\.mango$'), 'mango'),
)
LP_REGEXS_URL = (
    # 'http://map.naver.com/local/siteview.nhn?code=21149144'
    # 'http://m.map.naver.com/siteview.nhn?code=31176899'
    #(re_compile(r'^https?://.*map\.naver\.com/.*\?code=(?P<PlaceId>[0-9]+)&?.*$'), 'naver'),

    # 'http://map.naver.com/?app=Y&version=10&appMenu=location&pinId=31130096&pinType=site&lat=37.3916387&lng=127.0584149&title=능이향기&dlevel=11'
    # 'https://m.map.naver.com/viewer/map.nhn?pinType=site&pinId=21652462'
    #(re_compile(r'^https?://.*map\.naver\.com/.*\?.*pinId=(?P<PlaceId>[0-9]+)&?.*$'), 'naver'),

    # 'http://m.store.naver.com/restaurants/detail?id=37333252'
    #(re_compile(r'^https?://m\.store\.naver\.com/[A-za-z0-9_\-]+/detail\?id=(?P<PlaceId>[0-9]+)&?.*$'), 'naver'),


    # 'https://place.kakao.com/places/14720610/홍콩'
    (re_compile(r'^https?://place\.kakao\.com/places/(?P<PlaceId>[0-9]+)&?.*$'), 'kakao'),

    # 'http://m.map.daum.net/actions/detailInfoView?id=15493954'
    (re_compile(r'^https?://(m\.)?map\.daum\.net/actions/detailInfoView\?id=(?P<PlaceId>[0-9]+)&?.*$'), 'kakao'),

    # http://place.map.daum.net/26799590
    (re_compile(r'^https?://place\.map\.daum\.net/(?P<PlaceId>[0-9]+)&?.*$'), 'kakao'),

    # 'https://foursquare.com/v/방아깐/4ccffc63f6378cfaace1b1d6'
    (re_compile(r'^https?://.*foursquare\.com/v/.+/(?P<PlaceId>[a-z0-9]+)&?.*$'), '4square'),

    # 'http://foursquare.com/v/4ccffc63f6378cfaace1b1d6'
    (re_compile(r'^https?://.*foursquare\.com/v/(?P<PlaceId>[a-z0-9]+)&?.*$'), '4square'),

    # 'http://foursquare.com/v/4ccffc63f6378cfaace1b1d6'
    (re_compile(r'^https?://www\.mangoplate\.com/restaurants/(?P<PlaceId>[A-za-z0-9_\-]+)$'), 'mango'),

    # 'https://www.google.com/maps/place/Han+Ha+Rum+Korean+Restaurant/@22.3585964,113.5605519,9z/data=!4m8!1m2!2m1!1z7Iud64u5!3m4!1s0x34040056de2d51b3:0xae100fb893526bdf!8m2!3d22.2801408!4d114.182783'
    (re_compile(r'^https?://www\.google\.com/maps/place/(?P<PlaceName>.+)/@.+z/data=.*!3d(?P<lat>-?[0-9\.]+)!4d(?P<lon>-?[0-9\.]+).*$'), 'google'),
)

LP_TYPE = {'4square': 1, 'naver': 2, 'google': 3, 'kakao': 4, 'mango': 5,}


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
    def normalize_content(cls, raw_content):
        # uuid style
        for regex in LP_REGEXS:
            searcher = regex[0].search(raw_content)
            if searcher:
                return '%s.%s' % (searcher.group('PlaceId'), regex[1])

        # url style
        for regex in LP_REGEXS_URL:
            from base.legacy.urlnorm import norms
            raw_content = norms(raw_content)
            searcher = regex[0].search(raw_content)
            if searcher:
                d = searcher.groupdict()
                if 'PlaceId' in d:
                    return '%s.%s' % (d['PlaceId'], regex[1])
                elif 'PlaceName' in d and 'lon' in d and 'lat' in d:
                    google_place_id = cls.find_google_place_id_by_lonLatName(d['PlaceName'], d['lon'], d['lat'])
                    return '%s.%s' % (google_place_id, regex[1])
                else:
                    raise NotImplementedError
        return None

    @classmethod
    def find_google_place_id_by_lonLatName(cls, name, lon, lat, idx=None):
        api_key = get_api_key(idx)
        api_url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?key=%s&location=%s,%s&name=%s&rankby=distance' % (api_key, lat, lon, name)
        try:
            r = requests_get(api_url, timeout=60)
        except:
            return None
        if not r.status_code == status.HTTP_200_OK:
            return None

        d = json_loads(r.content)
        if 'status' not in d or d['status'] != 'OK':
            return None
        if 'results' not in d or not d['results'] or not d['results'][0] or 'place_id' not in d['results'][0]:
            return None
        return d['results'][0]['place_id']

    @property
    def _id(self):
        splits = self.content.split('.')
        if splits[1] == 'google':
            h = self.get_md5_hash(splits[0])
            h0 = hex(int(h[0], 16) | 8)[2:]
            return UUID('%s%s' % (h0, h[1:]))
        elif splits[1] == 'mango':
            h = ''.join([hex(ord(c))[2:] for c in splits[0]])
            return UUID(b'0000000%d%s' % (LP_TYPE[self.contentType], h.rjust(24, b'0')))
        else:
            return UUID(b'0000000%d%s' % (LP_TYPE[self.contentType], splits[0].rjust(24, b'0')))

    @property
    def url_for_access(self):
        splits = self.content.split('.')
        type = splits[1]
        key = splits[0]
        if type == 'naver':
            return 'http://map.naver.com/local/siteview.nhn?code=%s' % key
        elif type == 'kakao':
            return 'http://place.kakao.com/places/%s/' % key
        elif type == '4square':
            #return 'https://foursquare.com/v/%s' % splits[0]
            return '4square://%s' % key
        elif type == 'mango':
            return 'http://www.mangoplate.com/restaurants/%s' % key
        elif type == 'google':
            return 'google://%s' % key
        else:
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
            result = client.venues(url.split('//')[1])
        elif url.startswith('google'):
            result = self.access_force_google(url)
        else:
            raise NotImplementedError

        if result:
            result = json_dumps(result, ensure_ascii=False)
            file = Path(self.path_accessed)
            if not file.parent.exists():
                file.parent.mkdir(parents=True)
            summary = Path(self.path_summarized)
            if not Path(self.path_summarized).parent.exists():
                summary.parent.mkdir(parents=True)
            file.write_text(result)
            self._cache_accessed = result.replace('\r', '')

    @classmethod
    def access_force_google(cls, url, idx=None):
        api_key = get_api_key(idx)
        #headers = {'content-type': 'application/json'}
        key = url.split('//')[1]
        api_url = 'https://maps.googleapis.com/maps/api/place/details/json?key=%s&placeid=%s' % (api_key, key)
        try:
            r = requests_get(api_url, timeout=60)
        except:
            return None
        if not r.status_code == status.HTTP_200_OK:
            return None

        d = json_loads(r.content)
        if d['status'] != 'OK':
            return None
        return d

    @classmethod
    def get_from_url(cls, url):
        for regex in LP_REGEXS_URL:
            searcher = regex[0].search(url.content)
            if searcher:
                lp, is_created = cls.get_or_create_smart(url.content)
                return lp
        return None


    def summarize_force(self, accessed=None):
        # TODO : 각종 URL 패턴들에 대해 정보 수집하여 요약
        if not accessed:
            accessed = self.content_accessed

        json = None
        if accessed:
            if self.contentType == 'naver':
                #json = self.summarize_force_naver(accessed)
                raise NotImplementedError
            elif self.contentType == 'kakao':
                json = self.summarize_force_kakao(accessed)
            elif self.contentType == '4square':
                json = self.summarize_force_4square(accessed)
            elif self.contentType == 'mango':
                json = self.summarize_force_mango(accessed)
            elif self.contentType == 'google':
                json = self.summarize_force_google(accessed)
            else:
                raise NotImplementedError

        if json:
            from place.post import PostBase
            pb = PostBase(json)
            for img in pb.images:
                img.summarize()

    def summarize_force_naver(self, accessed):
        # TODO : 반드시 필요하게 되면... phantomjs 를 활용하여 다시 구현
        raise NotImplementedError
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
        return json

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
        return json

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
        return json

    def summarize_force_mango(self, accessed):
        # 파싱
        pq = PyQuery(accessed)
        #d = json_loads(pq('script[id="restaurant_info_json"]').html().strip().replace('&quot;', '"'))
        d = json_loads(pq('button[class="btn-map"]').attr('data-restaurant'))

        # 주요 정보
        lon = float(d['longitude'])
        lat = float(d['latitude'])
        name = d['name']
        phone = d['phone_number']
        if phone:
            phone = PhoneNumber.normalize_content(phone)
        addr = d['address']
        img_url = pq('meta[property="og:image"]').attr('content')

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
        ''' % (lon, lat, name, phone, addr, img_url, self.content,)

        f = Path(self.path_summarized)
        f.write_text(json)
        return json

    def summarize_force_google(self, accessed):
        # 파싱
        d = json_loads(accessed)['result']

        # 주요 정보
        lon = float(d['geometry']['location']['lng'])
        lat = float(d['geometry']['location']['lat'])
        name = d['name']
        phone = d.get('international_phone_number')
        if phone:
            phone = PhoneNumber.normalize_content(phone)
        addr_new = d.get('formatted_address')
        pr = None
        photos = d.get('photos')
        if photos:
            pr = photos[0]['photo_reference']
        img_url = None
        if pr:
            api_key = get_api_key()
            img_url = 'https://maps.googleapis.com/maps/api/place/photo?key=%s&maxwidth=1280&maxheight=1280&photoreference=%s' % (api_key, pr)
            print(img_url)

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
        return json

    def pre_save(self, is_created):
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
    def cjson(self):
        if self.timestamp:
            return dict(content=self.content, timestamp=self.timestamp)
        return dict(content=self.content)

    @property
    def content_for_search(self):
        return self.content.replace('#', '')

    # 관련 test 는 tag/test_models.py 에
    def process_tag_realtime(self):
        from tag.models import Tag, PlaceNoteTag
        tags = Tag.tags_from_note(self)
        for tag in tags:
            PlaceNoteTag.objects.get_or_create(tag=tag, placeNote=self)

    @classmethod
    def get_or_create_smart(cls, raw_content):
        instance, is_created = super(PlaceNote, cls).get_or_create_smart(raw_content)
        if is_created:
            instance.process_tag_realtime()
        return instance, is_created

    @property
    def is_only_for_tag(self):
        return self.content.startswith('[NOTE_TAGS]')


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

    @classmethod
    def normalize_content(cls, raw_content):
        return raw_content.strip().replace(' ', '').replace('#', '').replace(',', '').replace('"', '').replace("'", "")

    @property
    def is_remove(self):
        return self.content.startswith('-')

    @property
    def remove_target(self):
        if not self.is_remove:
            return None
        target_content = self.content[1:]
        target, is_created = self.get_or_create_smart(target_content)
        return target
