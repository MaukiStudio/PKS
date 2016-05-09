#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.response import Response
from rest_framework import status
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance
from django.db.models import F

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
            p = GEOSGeometry('POINT(%f %f)' % (lon, lat), srid=4326)
            return self.queryset.filter(lonLat__distance_lte=(p, D(m=r))).annotate(distance=Distance('lonLat', p)).order_by('distance')
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
        # TODO : 2개의 VD 에 같은 place 에 매핑되는 uplace 가 있는 경우 처리
        qs1 = self.queryset.filter(vd_id__in=self.vd.realOwner_vd_ids)
        # TODO : 리팩토링
        qs1 = qs1.filter(mask=F('mask').bitand(~1))
        if 'lon' in params and 'lat' in params:
            r = int(params.get('r', 1000))
            lon = float(params['lon'])
            lat = float(params['lat'])
            p = GEOSGeometry('POINT(%f %f)' % (lon, lat), srid=4326)
            if r == 0:
                qs2 = qs1.exclude(lonLat=None)
            else:
                qs2 = qs1.filter(lonLat__distance_lte=(p, D(m=r)))
            return qs2.annotate(distance=Distance('lonLat', p)).order_by('distance')
        return qs1.order_by('-modified')

    def create(self, request, *args, **kwargs):
        # TODO : 향후 remove mode 구현하기

        # vd 조회
        vd = self.vd
        if not vd: return Response(status=status.HTTP_401_UNAUTHORIZED)

        # 결과 처리를 위한 변수 선언
        uplace = None


        #######################################
        # 삭제 포스트 처리
        #######################################
        if 'remove' in request.data and request.data['remove']:
            # PostBase instance 생성
            pb = PostBase(request.data['remove'])
            if 'place_id' in request.data and request.data['place_id']:
                pb.place_id = request.data['place_id']
            if 'uplace_uuid' in request.data and request.data['uplace_uuid']:
                pb.uplace_uuid = request.data['uplace_uuid']

            # 삭제 포스트는 반드시 uplace_uuid 가 지정되어야 한다.
            uplace = UserPlace.get_from_uuid(pb.uplace_uuid)
            if not uplace:
                raise ValueError('삭제 포스트 처리 시에는 반드시 uplace_uuid 가 지정되어야 함')

            # 삭제 PostPiece 생성
            pp = PostPiece.objects.create(is_remove=True, place=None, uplace=uplace, vd=vd, data=pb.json)


        #######################################
        # 추가 포스트 처리
        #######################################
        if 'add' in request.data and request.data['add']:
            # PostBase instance 생성
            pb = PostBase(request.data['add'])
            if 'place_id' in request.data and request.data['place_id']:
                pb.place_id = request.data['place_id']
            if 'uplace_uuid' in request.data and request.data['uplace_uuid']:
                pb.uplace_uuid = request.data['uplace_uuid']

            # 추가 정보 가져오기 : 유저가 직접 입력했다고 봐도 무방한 사항만
            pb.load_additional_info()

            # UserPlace/Place 찾기
            uplace = UserPlace.get_from_post(pb, vd)
            pb.uplace_uuid = uplace.uuid

            # valid check
            if not pb.is_valid(uplace):
                raise ValueError('PostPiece 생성을 위한 최소한의 정보도 없음')

            # PostPiece 생성
            pp = PostPiece.objects.create(place=None, uplace=uplace, vd=vd, data=pb.json)

            # 임시적인 어드민 구현을 위해, MAMMA 가 추가로 뽑아준 post 가 있으면 추가로 포스팅
            pb_MAMMA = pb.pb_MAMMA
            if pb_MAMMA:
                # 아래 호출에서 Place 가 생성되고, 필요시 Place PostPiece 도 생성됨
                # TODO : 좀 더 Readability 가 높은 형태로 리팩토링
                uplace = UserPlace.get_from_post(pb_MAMMA, vd)

            # TODO : 튜닝 필요
            lonLat = (pb_MAMMA and pb_MAMMA.lonLat) or pb.lonLat
            if lonLat and uplace.place and not uplace.place.lonLat:
                uplace.place.lonLat = lonLat
                uplace.place.save()
            uplace.lonLat = uplace.lonLat or lonLat
            uplace.modified = get_timestamp()
            uplace.save()


        #######################################
        # 결과 처리
        #######################################
        serializer = self.get_serializer(uplace)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
