#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.response import Response
from rest_framework import status
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.measure import D

from place.models import Place, UserPlace, PostPiece
from place.serializers import PlaceSerializer, UserPlaceSerializer, PostPieceSerializer
from base.views import BaseViewset
from place.post import PostBase
from base.utils import get_timestamp


class PlaceViewset(BaseViewset):
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer

    def get_queryset(self):
        params = self.request.query_params
        if 'lon' in params and 'lat' in params:
            r = int(params.get('r', 1000))
            lon = float(params['lon'])
            lat = float(params['lat'])
            p = GEOSGeometry('POINT(%f %f)' % (lon, lat))
            return self.queryset.filter(lonLat__distance_lte=(p, D(m=r)))
        return super(PlaceViewset, self).get_queryset()


class PostPieceViewset(BaseViewset):
    queryset = PostPiece.objects.all()
    serializer_class = PostPieceSerializer


class UserPlaceViewset(BaseViewset):
    queryset = UserPlace.objects.all()
    serializer_class = UserPlaceSerializer

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
        # TODO : 향후 remove mode 구현하기

        # vd 조회
        vd = self.vd
        if not vd: return Response(status=status.HTTP_401_UNAUTHORIZED)

        # Post instance 생성
        pb = PostBase(request.data['add'])
        if 'place_id' in request.data and request.data['place_id']:
            pb.place_id = request.data['place_id']
        if 'uplace_uuid' in request.data and request.data['uplace_uuid']:
            pb.uplace_uuid = request.data['uplace_uuid']

        # UserPlace/Place 찾기
        uplace = UserPlace.get_from_post(pb, vd)

        # valid check
        if not pb.is_valid(uplace):
            raise ValueError('PostPiece 생성을 위한 최소한의 정보도 없음')

        # PostPiece 생성
        pp = PostPiece.objects.create(type_mask=0, place=None, uplace=uplace, vd=vd, data=pb.json)

        # 임시적인 어드민 구현을 위해, MAMMA 가 추가로 뽑아준 post 가 있으면 추가로 포스팅
        # TODO : 향후 Django-Celery 구조 도입하여 정리한 후 제거
        pb_MAMMA = pb.pb_MAMMA
        if pb_MAMMA:
            # TODO : Place 생성을 확인하기 위해 get_from_post() 를 호출하는 것은 적절한 구조가 아니다...
            uplace = UserPlace.get_from_post(pb_MAMMA, vd)
            pp2 = uplace.place.pps.first()
            if not pp2:
                pp2 = PostPiece.objects.create(type_mask=2, place=uplace.place, uplace=None, vd=vd, data=pb_MAMMA.json)

        # TODO : 튜닝 필요
        lonLat = (pb_MAMMA and pb_MAMMA.lonLat) or pb.lonLat
        if lonLat and uplace.place and not uplace.place.lonLat:
            uplace.place.lonLat = lonLat
            uplace.place.save()
        uplace.lonLat = uplace.lonLat or lonLat
        uplace.modified = get_timestamp()
        uplace.save()

        # 결과 리턴
        serializer = self.get_serializer(uplace)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
