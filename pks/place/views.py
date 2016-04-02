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
from content.models import FsVenue, ShortText
from image.models import Image


class PlaceViewset(ModelViewSet):
    queryset = models.Place.objects.all()
    serializer_class = serializers.PlaceSerializer


class PlaceContentViewset(ModelViewSet):
    queryset = models.PlaceContent.objects.all()
    serializer_class = serializers.PlaceContentSerializer


class UserPostViewset(ModelViewSet):
    queryset = models.UserPost.objects.all()
    serializer_class = serializers.UserPostSerializer

    def create(self, request, *args, **kwargs):
        # TODO : 리팩토링
        vd_id = request.session[VD_SESSION_KEY]
        vd = VD.objects.get(id=vd_id)
        if not vd: return Response(status=status.HTTP_401_UNAUTHORIZED)

        # TODO : add 외에 remove 도 구현, 기타 다른 create mode 는 지원하지 않음
        add = json_loads(request.data['add'])

        # TODO : place_id 가 없는 경우에 대한 구현 제대로
        place_id = add['place_id']

        place = models.Place.objects.get(id=place_id)
        if not place: return Response(status=status.HTTP_400_BAD_REQUEST)

        # add 를 이용한 post create (기존 post + add) 시에는 notes 및 urls 는 0개 혹은 1개만 허용된다.
        if 'notes' in add and add['notes'] and len(add['notes']) > 1:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if 'urls' in add and add['urls'] and len(add['urls']) > 1:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # 반복 처리 없는 Content
        lonLat = None; url = None; fsVenue = None
        if 'lonLat' in add and add['lonLat']:
            lonLat = GEOSGeometry('POINT(%f %f)' % (add['lonLat']['lon'], add['lonLat']['lat']))
        if 'urls' in add and add['urls'] and add['urls'][0]:
            url = Url.get_from_uuid(add['urls'][0]['uuid'])
        if 'fsVenue' in add and add['fsVenue']:
            fsVenue = FsVenue.get_from_uuid(add['fsVenue']['uuid'])

        # images
        first_image = None
        saved = False
        if 'images' in add and add['images'] and add['images'][0]:
            first_image = Image.get_from_uuid(add['images'][0]['uuid'])
            # json 에 넘어온 순서대로 조회되도록 reverse 한다
            for d in reversed(add['images']):
                img = Image.get_from_uuid(d['uuid'])
                imgNote = None; stxt_type = None
                if 'note' in d and d['note']:
                    imgNote = ShortText.get_from_uuid(d['note']['uuid'])
                    if imgNote: stxt_type = models.STXT_TYPE_IMAGE_NOTE
                else:
                    # 첫번째 이미지인데 이미지노트가 없다면? 여기서 저장하지 않고 하단에서 저장
                    if img == first_image: continue
                pc = models.PlaceContent(place=place, vd=vd, lonLat=lonLat, url=url, fsVenue=fsVenue,
                                         image=img, stxt_type=stxt_type, stxt=imgNote,)
                pc.save(); saved = True

        # stxts
        stxts = list()
        if 'name' in add and add['name']:
            stxts.append((models.STXT_TYPE_PLACE_NAME, ShortText.get_from_uuid(add['name']['uuid'])))
        if 'addr' in add and add['addr']:
            stxts.append((models.STXT_TYPE_ADDRESS, ShortText.get_from_uuid(add['addr']['uuid'])))
        if 'notes' in add and add['notes'] and add['notes'][0]:
            stxts.append((models.STXT_TYPE_PLACE_NOTE, ShortText.get_from_uuid(add['notes'][0]['uuid'])))
        for stxt in stxts:
            # image 가 여러개인 경우는 첫번째 이미지만 place stxt 와 같은 transaction 에 배치된다.
            pc = models.PlaceContent(place=place, vd=vd, lonLat=lonLat, url=url, fsVenue=fsVenue,
                                     image=first_image, stxt_type=stxt[0], stxt=stxt[1],)
            pc.save(); saved = True

        # 한번도 저장되지 않았다면? 최소 1회는 저장
        if not saved:
            pc = models.PlaceContent(place=place, vd=vd, lonLat=lonLat, url=url, fsVenue=fsVenue, image=first_image,)
            pc.save()

        post, created = models.UserPost.objects.get_or_create(vd=vd, place=place)
        serializer = self.get_serializer(post)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
