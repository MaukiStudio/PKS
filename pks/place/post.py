#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from json import loads as json_loads, dumps as json_dumps
from django.contrib.gis.geos import GEOSGeometry

from url.models import Url
from content.models import LegacyPlace, ShortText, PhoneNumber
from image.models import Image
from base.utils import get_timestamp
from content.models import LP_REGEXS_URL

# stxt_type
STXT_TYPE_PLACE_NOTE = 1
STXT_TYPE_PLACE_NAME = 2
STXT_TYPE_POS_DESC = 3
STXT_TYPE_IMAGE_NOTE = 4
STXT_TYPE_ADDRESS = 5
STXT_TYPE_REMOVE_CONTENT = 254


# TODO : 향후 삭제 처리 구현 필요. 특정 Content 를 삭제하고 싶은 경우 노트타입을 삭제로 붙임. 이 노트타입은 노트뿐만 아니라 다른 Content 에도 적용
class Post(object):

    def __init__(self, value=None):
        t = type(value)
        if t is int or t is long:
            self.json = dict(place_id=value, lonLat=None, images=list(), urls=list(), lps=list(),
                             name=None, notes=list(), posDesc=None, addrs=list(), phone=None,)
            self._json_str = None
        elif t is unicode or t is str:
            self._json_str = value
            self.json = json_loads(value)
        elif t is dict:
            self.json = value
            self._json_str = None
        else:
            raise NotImplementedError

    @property
    def json_str(self):
        if not self._json_str:
            self._json_str = json_dumps(self.json)
        return self._json_str

    def add_pc(self, pc):
        # Clear cache
        self._json_str = None

        if pc.lonLat and not self.json['lonLat']:
            self.json['lonLat'] = dict(lon=pc.lonLat.x, lat=pc.lonLat.y, timestamp=pc.timestamp)

        if pc.image:
            uuid = pc.image.uuid
            dl = self.json['images']
            if uuid not in [d['uuid'] for d in dl]:
                dl.append(dict(uuid=uuid, content=pc.image.content, note=None, timestamp=pc.timestamp, summary=pc.image.url_summarized))
            if pc.stxt_type == STXT_TYPE_IMAGE_NOTE and pc.stxt.content:
                d = None
                for dt in dl:
                    if dt['uuid'] == uuid:
                        d = dt
                        break
                if d and not d['note']:
                    d['note'] = dict(uuid=pc.stxt.uuid, content=pc.stxt.content, timestamp=pc.timestamp)

        if pc.url:
            uuid = pc.url.uuid
            dl = self.json['urls']
            if uuid not in [d['uuid'] for d in dl]:
                dl.append(dict(uuid=uuid, content=pc.url.content, timestamp=pc.timestamp))

        if pc.lp:
            uuid = pc.lp.uuid
            dl = self.json['lps']
            if uuid not in [d['uuid'] for d in dl]:
                dl.append(dict(uuid=uuid, content=pc.lp.content, timestamp=pc.timestamp))

        if pc.phone and not self.json['phone']:
            self.json['phone'] = dict(uuid=pc.phone.uuid, content=pc.phone.content, timestamp=pc.timestamp)

        if pc.stxt:
            uuid = pc.stxt.uuid
            if pc.stxt_type == STXT_TYPE_PLACE_NAME:
                if not self.json['name']:
                    self.json['name'] = dict(uuid=uuid, content=pc.stxt.content, timestamp=pc.timestamp)
            elif pc.stxt_type == STXT_TYPE_PLACE_NOTE:
                dl = self.json['notes']
                if uuid not in [d['uuid'] for d in dl]:
                    dl.append(dict(uuid=uuid, content=pc.stxt.content, timestamp=pc.timestamp))
            elif pc.stxt_type == STXT_TYPE_POS_DESC:
                if not self.json['posDesc']:
                    self.json['posDesc'] = dict(uuid=uuid, content=pc.stxt.content, timestamp=pc.timestamp)
            elif pc.stxt_type == STXT_TYPE_ADDRESS:
                dl = self.json['addrs']
                if len(dl) <= 2 and uuid not in [d['uuid'] for d in dl]:
                    dl.append(dict(uuid=uuid, content=pc.stxt.content, timestamp=pc.timestamp))
            elif pc.stxt_type == STXT_TYPE_IMAGE_NOTE or pc.stxt_type is None:
                pass
            else:
                print(pc.stxt_type)
                raise NotImplementedError


    def isSubsetOf(self, other):
        def isSubsetOf_dict(d1, d2):
            if not d1: return True
            elif not d2: return False
            elif type(d2) is not dict: return False

            for key, value in d1.iteritems():
                if not value:
                    continue
                elif type(value) is dict:
                    if key not in d2 or not isSubsetOf_dict(value, d2[key]):
                        return False
                elif type(value) is list:
                    if key not in d2 or not isSubsetOf_list(value, d2[key]):
                        return False
                else:
                    if key not in d2 or value != d2[key]:
                        return False
            return True
        def isSubsetOf_list(l1, l2):
            if not l1: return True
            elif not l2: return False
            elif type(l2) is not list: return False
            elif len(l1) != len(l2): return False

            for key, value in enumerate(l1):
                if not value:
                    if l2[key]:
                        return False
                elif type(value) is dict:
                    if not isSubsetOf_dict(value, l2[key]):
                        return False
                elif type(value) is list:
                    if not isSubsetOf_list(value, l2[key]):
                        return False
                else:
                    if value != l2[key]:
                        return False
            return True
        return isSubsetOf_dict(self.json, other.json)

    # TODO : 미구현 상태. 구현해야 함
    @property
    def is_valid(self):
        return True


    def create_by_add(self, vd, place=None):
        from place.models import Place, PlaceContent, UserPlace
        #########################################
        # PREPARE PART
        #########################################

        # Variables
        add = self.json
        first_url = None; urls = list()
        lonLat = None
        phone = None
        first_lp = None; lps = list()
        first_stxt = (None, None); stxts = list()
        first_image = None; images = list()

        # urls 조회
        if 'urls' in add and add['urls']:
            for url in reversed(add['urls']):
                urls.append(Url.get_from_json(url))
        for url in urls:
            regex = LP_REGEXS_URL[0][0]
            searcher = regex.search(url.content)
            if searcher:
                # 어드민 구현을 위해 임시적으로 바로 정보를 땡겨온다
                # TODO : 향후 제대로 구현할 것 (Post 리팩토링, Django Celery 구조 등 도입 후)
                post_naver = url.content_summarized
                # 리팩토링 하고 구현하자 ㅠ_ㅜ

        if len(urls) > 0: first_url = urls.pop()

        # lonLat 조회
        if 'lonLat' in add and add['lonLat']:
            lonLat = GEOSGeometry('POINT(%f %f)' % (add['lonLat']['lon'], add['lonLat']['lat']))

        # phone 조회
        if 'phone' in add and add['phone']:
            phone = PhoneNumber.get_from_json(add['phone'])

        # lps 조회
        if 'lps' in add and add['lps']:
            for lp in reversed(add['lps']):
                lps.append(LegacyPlace.get_from_json(lp))
        if len(lps) > 0: first_lp = lps.pop()

        # stxts 조회
        if 'addrs' in add and add['addrs']:
            for addr in reversed(add['addrs']):
                stxts.append((STXT_TYPE_ADDRESS, ShortText.get_from_json(addr)))
        if 'notes' in add and add['notes']:
            for note in reversed(add['notes']):
                stxts.append((STXT_TYPE_PLACE_NOTE, ShortText.get_from_json(note)))
        if 'posDesc' in add and add['posDesc']:
            stxts.append((STXT_TYPE_POS_DESC, ShortText.get_from_json(add['posDesc'])))
        if 'name' in add and add['name']:
            stxts.append((STXT_TYPE_PLACE_NAME, ShortText.get_from_json(add['name'])))
        if len(stxts) > 0: first_stxt = stxts.pop()

        # images 조회
        if 'images' in add and add['images'] and add['images'][0]:
            first_image = Image.get_from_json(add['images'][0])
            # json 에 넘어온 순서대로 조회되도록 reverse 한다
            for d in reversed(add['images']):
                img = Image.get_from_json(d)
                stxt = first_stxt
                if 'note' in d and d['note']:
                    imgNote = ShortText.get_from_json(d['note'])
                    stxt_type = None
                    if imgNote: stxt_type = STXT_TYPE_IMAGE_NOTE
                    stxt = (stxt_type, imgNote)
                else:
                    # 첫번째 이미지인데 이미지노트가 없다면 images 에서는 뺀다 (first_image 로 저장되므로)
                    if img == first_image: continue
                images.append((img, stxt))

        # default lonLat 처리
        # TODO : 여러장의 사진에 포함된 GPS 위치를 모두 활용하여 default lonLat 계산
        if not lonLat and first_image and first_image.lonLat:
            lonLat = first_image.lonLat

        # place 조회
        if not place:
            if 'place_id' in add and add['place_id']:
                place = Place.objects.get(id=add['place_id'])
            else:
                # TODO : 다른 정보들을 최대한 활용하여, 가능한한 최대한 place 찾는 로직 구현
                pass

        # 포스팅을 위한 최소한의 정보가 넘어왔는지 확인
        if not (lonLat or first_url or first_lp or (place and (first_stxt or first_image))):
            raise ValueError('포스팅을 위한 최소한의 정보도 없음')

        # 결국 place 를 찾지 못한 경우는 생성
        if not place:
            place = Place.objects.create(lonLat=lonLat)

        #########################################
        # SAVE PART
        #########################################

        timestamp = get_timestamp()

        # images 저장 : post 시 올라온 list 상의 순서를 보존해야 함 (post 조회시에는 생성된 순서 역순으로 보여짐)
        for t in images:
            pc = PlaceContent(place=place, vd=vd, lonLat=lonLat, url=first_url, lp=first_lp,
                              image=t[0], stxt_type=t[1][0], stxt=t[1][1], phone=phone,)
            pc.save(timestamp=timestamp)
            timestamp += 1

        # stxts 저장
        for stxt in stxts:
            # image 가 여러개인 경우는 첫번째 이미지만 place stxt 와 같은 transaction 에 배치된다.
            pc = PlaceContent(place=place, vd=vd, lonLat=lonLat, url=first_url, lp=first_lp,
                              image=first_image, stxt_type=stxt[0], stxt=stxt[1], phone=phone,)
            pc.save(timestamp=timestamp)
            timestamp += 1

        # urls 저장
        for url in urls:
            pc = PlaceContent(place=place, vd=vd, lonLat=lonLat, url=url, lp=first_lp,
                              image=first_image, stxt_type=first_stxt[0], stxt=first_stxt[1], phone=phone,)
            pc.save(timestamp=timestamp)
            timestamp += 1

        # lps 저장
        for lp in lps:
            pc = PlaceContent(place=place, vd=vd, lonLat=lonLat, url=first_url, lp=lp,
                              image=first_image, stxt_type=first_stxt[0], stxt=first_stxt[1], phone=phone,)
            pc.save(timestamp=timestamp)
            timestamp += 1

        # base transaction(PlaceContent) 저장
        pc = PlaceContent(place=place, vd=vd, lonLat=lonLat, url=first_url, lp=first_lp,
                          image=first_image, stxt_type=first_stxt[0], stxt=first_stxt[1], phone=phone,)
        pc.save(timestamp=timestamp)
        timestamp += 1

        # 결과 처리
        if not place.lonLat and lonLat:
            place.lonLat = lonLat
            place.save()
        uplace, created = UserPlace.objects.get_or_create(vd=vd, place=place,)
        if not created:
            uplace.modified = timestamp
            uplace.lonLat = lonLat
            uplace.save()
        return uplace


    # TODO : add 외에 remove 도 구현, 기타 다른 create mode 는 지원하지 않음
    def create_by_remove(self, vd, place=None):
        raise NotImplementedError