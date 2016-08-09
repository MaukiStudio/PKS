#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from json import loads as json_loads

from content.models import LegacyPlace, PhoneNumber, PlaceName, Address, PlaceNote, ImageNote
from image.models import Image
from base.models import Point, Visit, Rating
from pyquery import PyQuery
from requests import Timeout
from base.utils import remove_list, is_valid_json_item, remove_duplicates


class PostBase(object):

    def __init__(self, json=None, timestamp=None):
        self.names = list()
        self.visits = list()
        self.ratings = list()
        self.points = list()
        self.phones = list()
        self.addrs1 = list()
        self.addrs2 = list()
        self.addrs3 = list()
        self.lps = list()
        self.urls = list()
        self.notes = list()
        self.images = list()

        self.place_id = None
        self.uplace_uuid = None
        self.by_MAMMA = False
        self.iplace_uuid = None

        self._cache_tags = None

        t = type(json)
        if json is None:
            pass
        elif t is unicode or t is str:
            self.setUp(json_loads(json), timestamp)
        elif t is dict:
            self.setUp(json, timestamp)
        else:
            print(t)
            print(json)
            raise NotImplementedError

    def copy(self):
        result = PostBase()
        result.names = self.names[:]
        result.visits = self.visits[:]
        result.ratings = self.ratings[:]
        result.points = self.points[:]
        result.phones = self.phones[:]
        result.addrs1 = self.addrs1[:]
        result.addrs2 = self.addrs2[:]
        result.addrs3 = self.addrs3[:]
        result.lps = self.lps[:]
        result.urls = self.urls[:]
        result.notes = self.notes[:]
        result.images = self.images[:]

        result.place_id = self.place_id
        result.uplace_uuid = self.uplace_uuid
        result.by_MAMMA = self.by_MAMMA
        result.iplace_uuid = self.iplace_uuid

        result._cache_tags = self._cache_tags and self._cache_tags[:]
        return result

    @property
    def name(self):
        return (self.names and self.names[0]) or None
    @name.setter
    def name(self, v):
        self.names.insert(0, v)

    @property
    def visit(self):
        return (self.visits and self.visits[0]) or None
    @visit.setter
    def visit(self, v):
        self.visits.insert(0, v)

    @property
    def rating(self):
        return (self.ratings and self.ratings[0]) or None
    @rating.setter
    def rating(self, v):
        self.ratings.insert(0, v)

    @property
    def point(self):
        return (self.points and self.points[0]) or None
    @point.setter
    def point(self, v):
        self.points.insert(0, v)

    @property
    def phone(self):
        return (self.phones and self.phones[0]) or None
    @phone.setter
    def phone(self, v):
        self.phones.insert(0, v)

    @property
    def addr1(self):
        return (self.addrs1 and self.addrs1[0]) or None
    @addr1.setter
    def addr1(self, v):
        self.addrs1.insert(0, v)

    @property
    def addr2(self):
        return (self.addrs2 and self.addrs2[0]) or None
    @addr2.setter
    def addr2(self, v):
        self.addrs2.insert(0, v)

    @property
    def addr3(self):
        return (self.addrs3 and self.addrs3[0]) or None
    @addr3.setter
    def addr3(self, v):
        self.addrs3.insert(0, v)

    @property
    def lonLat(self):
        return (self.points and self.points[0] and self.points[0].lonLat) or None
    @lonLat.setter
    def lonLat(self, v):
        self.point = Point(v)

    @property
    def image(self):
        return (self.images and self.images[0]) or None
    @image.setter
    def image(self, v):
        self.images.insert(0, v)

    @property
    def note(self):
        result = None
        if self.notes:
            for note in self.notes:
                if not note.is_only_for_tag:
                    result = note
                    break
        return result
    @note.setter
    def note(self, v):
        self.notes.insert(0, v)

    @property
    def addr(self):
        return self.addr1 or self.addr2 or self.addr3 or None


    # TODO : iplace_uuid 가 세팅된 경우 원본 소스의 최신 데이터를 가져오는 처리
    def update(self, other, add=True):
        if add:
            self.names = other.names + self.names
            self.visits = other.visits + self.visits
            self.ratings = other.ratings + self.ratings
            self.points = other.points + self.points
            self.phones = other.phones + self.phones
            self.addrs1 = other.addrs1 + self.addrs1
            self.addrs2 = other.addrs2 + self.addrs2
            self.addrs3 = other.addrs3 + self.addrs3
            self.lps = other.lps + self.lps
            self.urls = other.urls + self.urls
            self.notes = other.notes + self.notes
            self.images = other.images + self.images
            self.iplace_uuid = self.iplace_uuid or other.iplace_uuid
        else:
            self.names = remove_list(self.names, other.names)
            self.visits = remove_list(self.visits, other.visits)
            self.ratings = remove_list(self.ratings, other.ratings)
            self.points = remove_list(self.points, other.points)
            self.phones = remove_list(self.phones, other.phones)
            self.addrs1 = remove_list(self.addrs1, other.addrs1)
            self.addrs2 = remove_list(self.addrs2, other.addrs2)
            self.addrs3 = remove_list(self.addrs3, other.addrs3)
            self.lps = remove_list(self.lps, other.lps)
            self.urls = remove_list(self.urls, other.urls)
            self.notes = remove_list(self.notes, other.notes)
            self.images = remove_list(self.images, other.images)


    def setUp(self, json, timestamp=None):

        # name 조회
        if is_valid_json_item('name', json):
            name = PlaceName.get_from_json(json['name'])
            if name:
                self.names.append(name)

        # visit 조회
        if is_valid_json_item('visit', json):
            visit = Visit.get_from_json(json['visit'])
            if visit:
                self.visits.append(visit)

        # rating 조회
        if is_valid_json_item('rating', json):
            rating = Rating.get_from_json(json['rating'])
            if rating:
                self.ratings.append(rating)

        # lonLat 조회
        if is_valid_json_item('lonLat', json):
            point = Point.get_from_json(json['lonLat'])
            if point:
                self.points.append(point)

        # phone 조회
        if is_valid_json_item('phone', json):
            phone = PhoneNumber.get_from_json(json['phone'])
            if phone:
                self.phone = phone

        # addr1 조회
        if is_valid_json_item('addr1', json):
            addr1 = Address.get_from_json(json['addr1'])
            if addr1:
                self.addrs1.append(addr1)

        # addr2 조회
        if is_valid_json_item('addr2', json):
            addr2 = Address.get_from_json(json['addr2'])
            if addr2:
                self.addrs2.append(addr2)

        # addr3 조회
        if is_valid_json_item('addr3', json):
            addr3 = Address.get_from_json(json['addr3'])
            if addr3:
                self.addrs3.append(addr3)

        # lps 조회
        if is_valid_json_item('lps', json):
            for lp_json in json['lps']:
                lp = LegacyPlace.get_from_json(lp_json)
                if lp:
                    self.lps.append(lp)

        # urls 조회
        if is_valid_json_item('urls', json):
            from url.models import Url
            for url_json in json['urls']:
                url = Url.get_from_json(url_json)
                if url:
                    self.urls.append(url)

        # notes 조회
        if is_valid_json_item('notes', json):
            for note_json in json['notes']:
                note = PlaceNote.get_from_json(note_json)
                if note:
                    note.timestamp = timestamp
                    self.notes.append(note)

        # images 조회
        if is_valid_json_item('images', json):
            for img_json in json['images']:
                img = Image.get_from_json(img_json)
                if img:
                    if 'note' in img_json and img_json['note']:
                        note = ImageNote.get_from_json(img_json['note'])
                        if note:
                            note.timestamp = timestamp
                            img.note = note
                    self.images.append(img)

        # place_id, uplace_uuid, iplace_uuid 조회
        if is_valid_json_item('place_id', json):
            self.place_id = json['place_id']
        if is_valid_json_item('uplace_uuid', json):
            self.uplace_uuid = json['uplace_uuid']
        if is_valid_json_item('iplace_uuid', json):
            self.iplace_uuid = json['iplace_uuid']


    # TODO : 지식의 집단화 적용
    @property
    def json(self):
        json = dict()
        if self.names: json['name'] = self.name.json
        if self.visits: json['visit'] = self.visit.json
        if self.ratings: json['rating'] = self.rating.json
        if self.points: json['lonLat'] = self.point.json
        if self.phones: json['phone'] = self.phone.json
        if self.addrs1: json['addr1'] = self.addr1.json
        if self.addrs2: json['addr2'] = self.addr2.json
        if self.addrs3: json['addr3'] = self.addr3.json
        if self.lps: json['lps'] = [lp.json for lp in self.lps]
        if self.urls: json['urls'] = [url.json for url in self.urls]
        if self.notes: json['notes'] = [note.json for note in self.notes]
        if self.images: json['images'] = [img.json for img in self.images]
        if self.iplace_uuid: json['iplace_uuid'] = self.iplace_uuid
        if self.tags: json['tags'] = [tag.json for tag in self.tags]
        return json

    @property
    def cjson(self):
        json = dict()
        if self.names: json['name'] = self.name.cjson
        if self.visits: json['visit'] = self.visit.cjson
        if self.ratings: json['rating'] = self.rating.cjson
        if self.points: json['lonLat'] = self.point.cjson
        if self.phones: json['phone'] = self.phone.cjson
        if self.addrs1: json['addr1'] = self.addr1.cjson
        if self.addrs2: json['addr2'] = self.addr2.cjson
        if self.addrs3: json['addr3'] = self.addr3.cjson
        if self.lps: json['lps'] = [lp.cjson for lp in self.lps]
        if self.urls: json['urls'] = [url.cjson for url in self.urls]
        if self.notes: json['notes'] = [note.cjson for note in self.notes]
        if self.images: json['images'] = [img.cjson for img in self.images]
        if self.iplace_uuid: json['iplace_uuid'] = self.iplace_uuid
        if self.tags: json['tags'] = [tag.cjson for tag in self.tags]
        return json

    @property
    def ujson(self):
        json = dict()
        if self.names: json['name'] = self.name.ujson
        if self.visits: json['visit'] = self.visit.ujson
        if self.ratings: json['rating'] = self.rating.ujson
        if self.points: json['lonLat'] = self.point.ujson
        if self.phones: json['phone'] = self.phone.ujson
        if self.addrs1: json['addr1'] = self.addr1.ujson
        if self.addrs2: json['addr2'] = self.addr2.ujson
        if self.addrs3: json['addr3'] = self.addr3.ujson
        if self.lps: json['lps'] = [lp.ujson for lp in self.lps]
        if self.urls: json['urls'] = [url.ujson for url in self.urls]
        if self.notes: json['notes'] = [note.ujson for note in self.notes]
        if self.images: json['images'] = [img.ujson for img in self.images]
        if self.iplace_uuid: json['iplace_uuid'] = self.iplace_uuid
        if self.tags: json['tags'] = [tag.ujson for tag in self.tags]
        return json

    @property
    # TODO : cache expire logic 구현
    def tags(self):
        if self._cache_tags is None and self.notes:
            all_tags = sum([list(note.tags.all()) for note in reversed(self.notes)], [])
            result = list()
            for tag in all_tags:
                if tag.is_remove:
                    result = remove_list(result, [tag.remove_target])
                else:
                    result.append(tag)
            self._cache_tags = remove_duplicates(result)
        return self._cache_tags

    def add_lps_from_urls(self):
        if self.urls:
            for url in self.urls:
                lp = LegacyPlace.get_from_url(url)
                if lp and lp not in self.lps:
                    self.lps.append(lp)

    @property
    def pb_MAMMA(self):
        self.normalize()

        # TODO : lps 가 2개 이상인 경우 UserPlace 쪼개는 처리
        if self.lps and self.lps[0]:
            lp = self.lps[0]
            lp.summarize()
            result = lp.content_summarized
            result.uplace_uuid = self.uplace_uuid
            # 하기 사항은 상속받으면 안됨 : 장소화가 된 장소를 다른 장소로 장소화가 불가능해짐
            #result.place_id = self.place_id
            result.by_MAMMA = True
            return result
        return None

    def is_valid(self, uplace=None):
        if not uplace:
            uplace = self.uplace_uuid
        if not uplace:
            if (self.point and self.images) or self.urls or self.lps:
                return True
        else:
            if self.urls or self.point or self.phone or self.lps or self.name or self.notes or self.images or \
                self.addr1 or self.addr2 or self.addr3 or self.rating or self.visit:
                return True
        return False

    def normalize(self):
        self.add_lps_from_urls()

        self.names = remove_duplicates(self.names)
        self.visits = remove_duplicates(self.visits)
        self.ratings = remove_duplicates(self.ratings)
        self.points = remove_duplicates(self.points)
        self.phones = remove_duplicates(self.phones)
        self.addrs1 = remove_duplicates(self.addrs1)
        self.addrs2 = remove_duplicates(self.addrs2)
        self.addrs3 = remove_duplicates(self.addrs3)
        self.lps = remove_duplicates(self.lps)
        self.urls = remove_duplicates(self.urls)
        self.notes = remove_duplicates(self.notes)
        self.images = remove_duplicates(self.images)

        if self.lps:
            def lp_cmp(lp1, lp2):
                if lp1.place and not lp2.place:
                    return -1
                elif not lp1.place and lp2.place:
                    return 1
                lp_type1 = lp1.lp_type
                if lp_type1 in (2, 4): lp_type1 -= 5
                lp_type2 = lp2.lp_type
                if lp_type2 in (2, 4): lp_type2 -= 5
                return lp_type1 - lp_type2
            self.lps.sort(cmp=lp_cmp)


    # 추가 정보 가져오기 : 유저가 직접 입력했다고 봐도 무방한 사항만
    # TODO : 좀 더 깔끔하고 성능 좋게 리팩토링
    def load_additional_info(self):
        # 이미지가 없는 경우, URL 에서 이미지 가져오기
        if not self.images and self.urls and self.urls[0]:
            url = self.urls[0]
            try:
                url.access()
                pq = PyQuery(url.content_accessed)
                img_url = pq('meta[property="og:image"]').attr('content')
                if img_url:
                    img = Image.get_from_json('{"content": "%s"}' % img_url)
                    if img:
                        img.summarize()
                        self.images.append(img)
            except Timeout:
                pass

    def reset_except_region_property(self):
        self.names = list()
        self.visits = list()
        self.ratings = list()
        #self.points = list()
        self.phones = list()
        #self.addrs1 = list()
        #self.addrs2 = list()
        #self.addrs3 = list()
        self.lps = list()
        #self.urls = list()
        #self.notes = list()
        self.images = list()

        self.place_id = None
        self.uplace_uuid = None
        self.by_MAMMA = False
        self.iplace_uuid = None

        self._cache_tags = None
