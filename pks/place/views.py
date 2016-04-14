#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.response import Response
from rest_framework import status
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.measure import D

from place.models import Place, UserPlace, PlaceContent
from place.serializers import PlaceSerializer, UserPlaceSerializer, PlaceContentSerializer
from base.views import BaseViewset
from place.post import Post


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


class PlaceContentViewset(BaseViewset):
    queryset = PlaceContent.objects.all()
    serializer_class = PlaceContentSerializer


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
        #########################################
        # PREPARE PART
        #########################################

        # vd 조회
        vd = self.vd
        if not vd: return Response(status=status.HTTP_401_UNAUTHORIZED)

        # Post instance 생성
        post = Post(request.data['add'])

        # Post.create_by_add()
        uplace = None
        if 'uplace_uuid' in request.data and request.data['uplace_uuid']:
            uplace = UserPlace.get_from_uuid(request.data['uplace_uuid'])
        uplace = post.create_by_add(vd, uplace)

        # MAMMA 가 추가로 뽑아준 post 가 있으면 추가로 포스팅
        if post.post_MAMMA:
            uplace = post.post_MAMMA.create_by_add(vd, uplace)

        # 결과 리턴
        #uplace.clearCache()
        serializer = self.get_serializer(uplace)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
