#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from json import loads as json_loads

from content.models import LegacyPlace, PhoneNumber, PlaceName, Address, PlaceNote, ImageNote
from image.models import Image
from base.models import Point
from pyquery import PyQuery
from requests import Timeout


class PostBase(object):

    def __init__(self, json=None, timestamp=None):
        self.name = None
        self.point = None
        self.phone = None
        self.addr1 = None
        self.addr2 = None
        self.addr3 = None
        self.lps = list()
        self.urls = list()
        self.notes = list()
        self.images = list()

        self.place_id = None
        self.uplace_uuid = None

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

    @property
    def lonLat(self):
        if self.point:
            return self.point.lonLat
        return None


    def update(self, other, add=True):
        if add:
            if other.name: self.name = other.name
            if other.point: self.point = other.point
            if other.phone: self.phone = other.phone
            if other.addr1: self.addr1 = other.addr1
            if other.addr2: self.addr2 = other.addr2
            if other.addr3: self.addr3 = other.addr3
        else:
            if other.name == self.name: self.name = None
            if other.point == self.point: self.point = None
            if other.phone == self.phone: self.phone = None
            if other.addr1 == self.addr1: self.addr1 = None
            if other.addr2 == self.addr2: self.addr2 = None
            if other.addr3 == self.addr3: self.addr3 = None

        for lp in reversed(other.lps):
            try:
                self.lps.remove(lp)
            except ValueError:
                pass
            if add:
                self.lps.insert(0, lp)

        for url in reversed(other.urls):
            try:
                self.urls.remove(url)
            except ValueError:
                pass
            if add:
                self.urls.insert(0, url)

        for note in reversed(other.notes):
            try:
                self.notes.remove(note)
            except ValueError:
                pass
            if add:
                self.notes.insert(0, note)

        for image in reversed(other.images):
            old_same_image = None
            try:
                pos = self.images.index(image)
                old_same_image = self.images[pos]
                del self.images[pos]
            except ValueError:
                pass
            if add:
                if old_same_image and not image.note:
                    image.note = old_same_image.note
                self.images.insert(0, image)


    def is_valid_json_item(self, item_name, json):
        if item_name in json and json[item_name]:
            item_json = json[item_name]
            if 'content' in item_json:
                return item_json['content'] != 'None'
            else:
                return True
        return False

    def setUp(self, json, timestamp=None):

        # name 조회
        if self.is_valid_json_item('name', json):
            name = PlaceName.get_from_json(json['name'])
            if name:
                #name.timestamp = timestamp
                self.name = name

        # lonLat 조회
        if self.is_valid_json_item('lonLat', json):
            point = Point.get_from_json(json['lonLat'])
            if point:
                #point.timestamp = timestamp
                self.point = point

        # phone 조회
        if self.is_valid_json_item('phone', json):
            phone = PhoneNumber.get_from_json(json['phone'])
            if phone:
                #phone.timestamp = timestamp
                self.phone = phone

        # addr1 조회
        if self.is_valid_json_item('addr1', json):
            addr1 = Address.get_from_json(json['addr1'])
            if addr1:
                #addr1.timestamp = timestamp
                self.addr1 = addr1

        # addr2 조회
        if self.is_valid_json_item('addr2', json):
            addr2 = Address.get_from_json(json['addr2'])
            if addr2:
                #addr2.timestamp = timestamp
                self.addr2 = addr2

        # addr3 조회
        if self.is_valid_json_item('addr3', json):
            addr3 = Address.get_from_json(json['addr3'])
            if addr3:
                #addr3.timestamp = timestamp
                self.addr3 = addr3

        # lps 조회
        if self.is_valid_json_item('lps', json):
            for lp_json in json['lps']:
                lp = LegacyPlace.get_from_json(lp_json)
                if lp:
                    #lp.timestamp = timestamp
                    self.lps.append(lp)

        # urls 조회
        if self.is_valid_json_item('urls', json):
            from url.models import Url
            for url_json in json['urls']:
                url = Url.get_from_json(url_json)
                if url:
                    #url.timestamp = timestamp
                    self.urls.append(url)

        # notes 조회
        if self.is_valid_json_item('notes', json):
            for note_json in json['notes']:
                note = PlaceNote.get_from_json(note_json)
                if note:
                    note.timestamp = timestamp
                    self.notes.append(note)

        # images 조회
        if self.is_valid_json_item('images', json):
            for img_json in json['images']:
                img = Image.get_from_json(img_json)
                if img:
                    img.timestamp = timestamp
                    if 'note' in img_json and img_json['note']:
                        note = ImageNote.get_from_json(img_json['note'])
                        if note:
                            note.timestamp = timestamp
                            img.note = note
                    self.images.append(img)

        # place_id, uplace_uuid 조회
        if self.is_valid_json_item('place_id', json):
            self.place_id = json['place_id']
        if self.is_valid_json_item('uplace_uuid', json):
            self.uplace_uuid = json['uplace_uuid']


    @property
    def json(self):
        json = dict()
        if self.name: json['name'] = self.name.json
        if self.point: json['lonLat'] = self.point.json
        if self.phone: json['phone'] = self.phone.json
        if self.addr1: json['addr1'] = self.addr1.json
        if self.addr2: json['addr2'] = self.addr2.json
        if self.addr3: json['addr3'] = self.addr3.json
        if self.lps: json['lps'] = [lp.json for lp in self.lps]
        if self.urls: json['urls'] = [url.json for url in self.urls]
        if self.notes: json['notes'] = [note.json for note in self.notes]
        if self.images: json['images'] = [img.json for img in self.images]
        return json

    def add_lps_from_urls(self):
        for url in self.urls:
            lp = LegacyPlace.get_from_url(url)
            if lp and lp not in self.lps:
                self.lps.append(lp)

    @property
    def pb_MAMMA(self):
        # TODO : pb_MAMMA 호출 후에 self 가 변경되는 구조는 적절하지 않다
        self.add_lps_from_urls()
        self.sort()

        # TODO : lps 가 2개 이상인 경우 UserPlace 쪼개는 처리
        if self.lps and self.lps[0]:
            lp = self.lps[0]
            # TODO : 포스퀘어 요약 구현한 후 제거
            if lp.lp_type == 1:
                return None

            lp.summarize(timeout=3)
            result = lp.content_summarized
            result.uplace_uuid = self.uplace_uuid
            result.place_id = self.place_id
            return result
        return None

    def is_valid(self, uplace=None):
        if not uplace:
            if (self.point and self.images) or self.urls or self.lps:
                return True
        else:
            if self.urls or self.point or self.phone or self.lps or self.name or self.notes or self.images or \
                self.addr1 or self.addr2 or self.addr3:
                return True
        return False

    def sort(self):
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
