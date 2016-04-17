#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from json import loads as json_loads

from content.models import LegacyPlace, PhoneNumber, LP_REGEXS_URL, PlaceName, Address, PlaceNote, ImageNote
from image.models import Image
from base.models import Point


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

    def update(self, other):
        if other.name: self.name = other.name
        if other.point: self.point = other.point
        if other.phone: self.phone = other.phone
        if other.addr1: self.addr1 = other.addr1
        if other.addr2: self.addr2 = other.addr2
        if other.addr3: self.addr3 = other.addr3

        for lp in reversed(other.lps):
            try:
                self.lps.remove(lp)
            except ValueError:
                pass
            self.lps.insert(0, lp)

        for url in reversed(other.urls):
            try:
                self.urls.remove(url)
            except ValueError:
                pass
            self.urls.insert(0, url)

        for note in reversed(other.notes):
            try:
                self.notes.remove(note)
            except ValueError:
                pass
            self.notes.insert(0, note)

        for image in reversed(other.images):
            old_same_image = None
            try:
                pos = self.images.index(image)
                old_same_image = self.images[pos]
                del self.images[pos]
            except ValueError:
                pass
            if old_same_image and not image.note:
                image.note = old_same_image.note
            self.images.insert(0, image)

    def setUp(self, json, timestamp=None):

        # name 조회
        if 'name' in json and json['name']:
            name = PlaceName.get_from_json(json['name'])
            #name.timestamp = timestamp
            self.name = name

        # lonLat 조회
        if 'lonLat' in json and json['lonLat']:
            point = Point.get_from_json(json['lonLat'])
            #point.timestamp = timestamp
            self.point = point

        # phone 조회
        if 'phone' in json and json['phone']:
            phone = PhoneNumber.get_from_json(json['phone'])
            #phone.timestamp = timestamp
            self.phone = phone

        # addr1 조회
        if 'addr1' in json and json['addr1']:
            addr1 = Address.get_from_json(json['addr1'])
            #addr1.timestamp = timestamp
            self.addr1 = addr1

        # addr2 조회
        if 'addr2' in json and json['addr2']:
            addr2 = Address.get_from_json(json['addr2'])
            #addr2.timestamp = timestamp
            self.addr2 = addr2

        # addr3 조회
        if 'addr3' in json and json['addr3']:
            addr3 = Address.get_from_json(json['addr3'])
            #addr3.timestamp = timestamp
            self.addr3 = addr3

        # lps 조회
        if 'lps' in json and json['lps']:
            for lp_json in json['lps']:
                lp = LegacyPlace.get_from_json(lp_json)
                #lp.timestamp = timestamp
                self.lps.append(lp)

        # urls 조회
        if 'urls' in json and json['urls']:
            from url.models import Url
            for url_json in json['urls']:
                url = Url.get_from_json(url_json)
                #url.timestamp = timestamp
                self.urls.append(url)

        # notes 조회
        if 'notes' in json and json['notes']:
            for note_json in json['notes']:
                note = PlaceNote.get_from_json(note_json)
                note.timestamp = timestamp
                self.notes.append(note)

        # images 조회
        if 'images' in json and json['images']:
            for img_json in json['images']:
                img = Image.get_from_json(img_json)
                img.timestamp = timestamp
                if 'note' in img_json and img_json['note']:
                    note = ImageNote.get_from_json(img_json['note'])
                    if note:
                        note.timestamp = timestamp
                        img.note = note
                self.images.append(img)

        # place_id, uplace_uuid 조회
        if 'place_id' in json and json['place_id']:
            self.place_id = json['place_id']
        if 'uplace_uuid' in json and json['uplace_uuid']:
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

    @property
    def pb_MAMMA(self):
        for url in self.urls:
            regex = LP_REGEXS_URL[0][0]
            searcher = regex.search(url.content)
            if searcher:
                # TODO : 향후 제대로 구현할 것 (Django Celery 구조 등 도입 후)
                # 당장 어드민 구현을 위해, 네이버 MAP URL인 경우 임시적으로 바로 정보를 땡겨온다
                url.summarize()

                # 이미 요약되어 있으면 곧바로 처리되도록 함
                if url.is_summarized:
                    result = url.content_summarized
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
