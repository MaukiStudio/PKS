#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from json import loads as json_loads
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from django.contrib.gis.geos import GEOSGeometry

from place import models
from place import serializers
from account.models import VD
from pks.settings import VD_SESSION_KEY
from url.models import Url
from content.models import LegacyPlace, ShortText
from image.models import Image
from base.utils import get_timestamp


class PlaceViewset(ModelViewSet):
    queryset = models.Place.objects.all()
    serializer_class = serializers.PlaceSerializer


class PlaceContentViewset(ModelViewSet):
    queryset = models.PlaceContent.objects.all()
    serializer_class = serializers.PlaceContentSerializer


class UserPostViewset(ModelViewSet):
    queryset = models.UserPost.objects.all()
    serializer_class = serializers.UserPostSerializer

    def get_queryset(self):
        if 'ru' in self.request.query_params and self.request.query_params['ru'] == 'myself':
            # TODO : 리팩토링, vd=myself 구현을 진짜 ru=myself 구현으로 변경
            vd_id = self.request.session[VD_SESSION_KEY]
            return self.queryset.filter(vd_id=vd_id)
        return super(UserPostViewset, self).get_queryset()

    def create(self, request, *args, **kwargs):
        #########################################
        # PREPARE PART
        #########################################

        # vd 조회
        # TODO : 리팩토링
        vd_id = request.session[VD_SESSION_KEY]
        vd = VD.objects.get(id=vd_id)
        if not vd: return Response(status=status.HTTP_401_UNAUTHORIZED)

        # TODO : add 외에 remove 도 구현, 기타 다른 create mode 는 지원하지 않음
        # DRF 의 Test Client 쪽 버그로 인해 하기와 같이 구현해야 함
        add = request.data['add']
        if type(add) is str or type(add) is unicode:
            add = json_loads(add)

        # 단일 Content 조회
        lonLat = None; lp = None
        if 'lonLat' in add and add['lonLat']:
            lonLat = GEOSGeometry('POINT(%f %f)' % (add['lonLat']['lon'], add['lonLat']['lat']))
        if 'lp' in add and add['lp']:
            lp = LegacyPlace.get_from_json(add['lp'])

        # urls 조회
        first_url = None
        urls = list()
        if 'urls' in add and add['urls']:
            for url in reversed(add['urls']):
                urls.append(Url.get_from_json(url))
        if len(urls) > 0: first_url = urls.pop()

        # stxts 조회
        first_stxt = (None, None)
        stxts = list()
        if 'name' in add and add['name']:
            stxts.append((models.STXT_TYPE_PLACE_NAME, ShortText.get_from_json(add['name'])))
        if 'addr' in add and add['addr']:
            stxts.append((models.STXT_TYPE_ADDRESS, ShortText.get_from_json(add['addr'])))
        if 'notes' in add and add['notes']:
            for note in reversed(add['notes']):
                stxts.append((models.STXT_TYPE_PLACE_NOTE, ShortText.get_from_json(note)))
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
        if 'place_id' in add:
            place_id = add['place_id']
            place = models.Place.objects.get(id=place_id)

        # 포스팅을 위한 최소한의 정보가 넘어왔는지 확인
        if not (lonLat or first_url or lp or (place and (first_stxt or first_image))):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # place_id 가 넘어오지 않은 경우
        if not place:
            # TODO : place_id 가 없는 경우에 대한 구현 제대로
            place = models.Place.objects.create()

        #########################################
        # SAVE PART
        #########################################

        timestamp = get_timestamp()

        # images 저장 : post 시 올라온 list 상의 순서를 보존해야 함 (post 조회시에는 생성된 순서 역순으로 보여짐)
        for t in images:
            pc = models.PlaceContent(place=place, vd=vd, lonLat=lonLat, url=first_url, lp=lp,
                                     image=t[0], stxt_type=t[1][0], stxt=t[1][1],)
            pc.save(timestamp=timestamp)
            timestamp += 1

        # stxts 저장
        for stxt in stxts:
            # image 가 여러개인 경우는 첫번째 이미지만 place stxt 와 같은 transaction 에 배치된다.
            pc = models.PlaceContent(place=place, vd=vd, lonLat=lonLat, url=first_url, lp=lp,
                                     image=first_image, stxt_type=stxt[0], stxt=stxt[1],)
            pc.save(timestamp=timestamp)
            timestamp += 1

        # urls 저장
        for url in urls:
            pc = models.PlaceContent(place=place, vd=vd, lonLat=lonLat, url=url, lp=lp,
                                     image=first_image, stxt_type=first_stxt[0], stxt=first_stxt[1])
            pc.save(timestamp=timestamp)
            timestamp += 1

        # base transaction(PlaceContent) 저장
        pc = models.PlaceContent(place=place, vd=vd, lonLat=lonLat, url=first_url, lp=lp,
                                 image=first_image, stxt_type=first_stxt[0], stxt=first_stxt[1])
        pc.save(timestamp=timestamp)
        timestamp += 1

        # 결과 처리
        post, created = models.UserPost.objects.get_or_create(vd=vd, place=place)
        serializer = self.get_serializer(post)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
