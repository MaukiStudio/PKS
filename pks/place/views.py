#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from json import loads as json_loads
from rest_framework.response import Response
from rest_framework import status
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.measure import D

from place import models
from place import serializers
from url.models import Url
from content.models import LegacyPlace, ShortText, PhoneNumber
from image.models import Image
from base.utils import get_timestamp
from base.views import BaseViewset


class PlaceViewset(BaseViewset):
    queryset = models.Place.objects.all()
    serializer_class = serializers.PlaceSerializer

    def get_queryset(self):
        params = self.request.query_params
        if 'lon' in params and 'lat' in params:
            r = int(params.get('r', 1000))
            lon = float(params['lon'])
            lat = float(params['lat'])
            p = GEOSGeometry('POINT(%f %f)' % (lon, lat))
            return self.queryset.filter(lonLat__distance_lte=(p, D(m=r)))
        return super(PlaceViewset, self).get_queryset()


class PlaceContentViewset(BaseViewset):
    queryset = models.PlaceContent.objects.all()
    serializer_class = serializers.PlaceContentSerializer


class UserPlaceViewset(BaseViewset):
    queryset = models.UserPlace.objects.all()
    serializer_class = serializers.UserPlaceSerializer

    def get_queryset(self):
        params = self.request.query_params
        if 'ru' in params and params['ru'] != 'myself':
            raise NotImplementedError('Now, ru=myself only')
        qs1 = self.queryset.filter(vd_id__in=self.vd.realOwner_vd_ids)
        if 'lon' in params and 'lat' in params:
            r = int(params.get('r', 1000))
            lon = float(params['lon'])
            lat = float(params['lat'])
            p = GEOSGeometry('POINT(%f %f)' % (lon, lat))
            return qs1.filter(lonLat__distance_lte=(p, D(m=r)))
        return qs1.order_by('-modified')

    def create(self, request, *args, **kwargs):
        #########################################
        # PREPARE PART
        #########################################

        # vd 조회
        vd = self.vd
        if not vd: return Response(status=status.HTTP_401_UNAUTHORIZED)

        # TODO : add 외에 remove 도 구현, 기타 다른 create mode 는 지원하지 않음
        # DRF 의 Test Client 쪽 버그로 인해 하기와 같이 구현해야 함
        add = request.data['add']
        if type(add) is str or type(add) is unicode:
            add = json_loads(add)

        # Simple Property 조회 : 현재는 lonLat 뿐임
        lonLat = None
        if 'lonLat' in add and add['lonLat']:
            lonLat = GEOSGeometry('POINT(%f %f)' % (add['lonLat']['lon'], add['lonLat']['lat']))

        # phone 조회
        phone = None
        if 'phone' in add and add['phone']:
            phone = PhoneNumber.get_from_json(add['phone'])

        # lps 조회
        first_lp = None
        lps = list()
        if 'lps' in add and add['lps']:
            for lp in reversed(add['lps']):
                lps.append(LegacyPlace.get_from_json(lp))
        if len(lps) > 0: first_lp = lps.pop()

        # urls 조회
        first_url = None
        urls = list()
        if 'urls' in add and add['urls']:
            for url in reversed(add['urls']):
                urls.append(Url.get_from_json(url))
        if len(urls) > 0: first_url = urls.pop()

        # stxts 조회
        # stxts 에는 우선순위가 낮은 것부터 먼저 append 한다
        first_stxt = (None, None)
        stxts = list()
        if 'addrs' in add and add['addrs']:
            for addr in reversed(add['addrs']):
                stxts.append((models.STXT_TYPE_ADDRESS, ShortText.get_from_json(addr)))
        if 'posDesc' in add and add['posDesc']:
            stxts.append((models.STXT_TYPE_POS_DESC, ShortText.get_from_json(add['posDesc'])))
        if 'notes' in add and add['notes']:
            for note in reversed(add['notes']):
                stxts.append((models.STXT_TYPE_PLACE_NOTE, ShortText.get_from_json(note)))
        if 'name' in add and add['name']:
            stxts.append((models.STXT_TYPE_PLACE_NAME, ShortText.get_from_json(add['name'])))
        if len(stxts) > 0: first_stxt = stxts.pop()

        # images 조회
        first_image = None
        images = list()
        if 'images' in add and add['images'] and add['images'][0]:
            first_image = Image.get_from_json(add['images'][0])
            # json 에 넘어온 순서대로 조회되도록 reverse 한다
            for d in reversed(add['images']):
                img = Image.get_from_json(d)
                stxt = first_stxt
                if 'note' in d and d['note']:
                    imgNote = ShortText.get_from_json(d['note'])
                    stxt_type = None
                    if imgNote: stxt_type = models.STXT_TYPE_IMAGE_NOTE
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
        place = None
        if 'place_id' in add and add['place_id']:
            place = models.Place.objects.get(id=add['place_id'])
        elif 'place_id' in request.data and request.data['place_id']:
            place = models.Place.objects.get(id=request.data['place_id'])

        # 포스팅을 위한 최소한의 정보가 넘어왔는지 확인
        if not (lonLat or first_url or first_lp or (place and (first_stxt or first_image))):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # place_id 가 넘어오지 않은 경우
        if not place:
            # TODO : place_id 가 없는 경우에 대한 구현 제대로
            place = models.Place.objects.create(lonLat=lonLat)

        #########################################
        # SAVE PART
        #########################################

        timestamp = get_timestamp()

        # images 저장 : post 시 올라온 list 상의 순서를 보존해야 함 (post 조회시에는 생성된 순서 역순으로 보여짐)
        for t in images:
            pc = models.PlaceContent(place=place, vd=vd, lonLat=lonLat, url=first_url, lp=first_lp,
                                     image=t[0], stxt_type=t[1][0], stxt=t[1][1], phone=phone,)
            pc.save(timestamp=timestamp)
            timestamp += 1

        # stxts 저장
        for stxt in stxts:
            # image 가 여러개인 경우는 첫번째 이미지만 place stxt 와 같은 transaction 에 배치된다.
            pc = models.PlaceContent(place=place, vd=vd, lonLat=lonLat, url=first_url, lp=first_lp,
                                     image=first_image, stxt_type=stxt[0], stxt=stxt[1], phone=phone,)
            pc.save(timestamp=timestamp)
            timestamp += 1

        # urls 저장
        for url in urls:
            pc = models.PlaceContent(place=place, vd=vd, lonLat=lonLat, url=url, lp=first_lp,
                                     image=first_image, stxt_type=first_stxt[0], stxt=first_stxt[1], phone=phone,)
            pc.save(timestamp=timestamp)
            timestamp += 1

        # lps 저장
        for lp in lps:
            pc = models.PlaceContent(place=place, vd=vd, lonLat=lonLat, url=first_url, lp=lp,
                                     image=first_image, stxt_type=first_stxt[0], stxt=first_stxt[1], phone=phone,)
            pc.save(timestamp=timestamp)
            timestamp += 1

        # base transaction(PlaceContent) 저장
        pc = models.PlaceContent(place=place, vd=vd, lonLat=lonLat, url=first_url, lp=first_lp,
                                 image=first_image, stxt_type=first_stxt[0], stxt=first_stxt[1], phone=phone,)
        pc.save(timestamp=timestamp)
        timestamp += 1

        # 결과 처리
        if not place.lonLat and lonLat:
            place.lonLat = lonLat
            place.save()
        uplace, created = models.UserPlace.objects.get_or_create(vd=vd, place=place,)
        if not created:
            uplace.modified = timestamp
            uplace.lonLat = lonLat
            uplace.save()
        serializer = self.get_serializer(uplace)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
