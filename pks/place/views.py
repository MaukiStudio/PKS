#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.response import Response
from rest_framework import status
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance
from rest_framework.decorators import list_route, detail_route

from place.models import Place, UserPlace, PostPiece, RADIUS_LOCAL_RANGE
from place.serializers import PlaceSerializer, UserPlaceSerializer, PostPieceSerializer
from base.views import BaseViewset
from place.post import PostBase
from base.utils import get_timestamp
from base.cache import cache_expire_ru


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

    # TODO : filter_queryset() 이용한 리팩토링
    def get_queryset(self):
        params = self.request.query_params
        if 'ru' in params and params['ru'] != 'myself':
            # Now, ru=myself only
            raise NotImplementedError

        order_by = None
        if 'order_by' in params and params['order_by']:
            if params['order_by'] in ('modified', '-modified'):
                order_by = params['order_by']
            elif params['order_by'] in ('distance_from_origin', '-distance_from_origin'):
                order_by = params['order_by'].split('_')[0]

        from place.libs import get_proper_uplaces_qs
        qs = get_proper_uplaces_qs(self.vd)

        # 장소화되지 않은 uplace 조회
        if 'placed' in params and params['placed']:
            if params['placed'].lower() in ('true', 'yes', '1', 'ok'):
                qs = qs.exclude(place=None)
            else:
                qs = qs.filter(place=None)

        origin = None
        if 'lon' in params and 'lat' in params:
            r = int(params.get('r', 1000))
            lon = float(params['lon'])
            lat = float(params['lat'])
            origin = GEOSGeometry('POINT(%f %f)' % (lon, lat), srid=4326)
            if r == 0:
                qs = qs.exclude(lonLat=None)
            else:
                qs = qs.filter(lonLat__distance_lte=(origin, D(m=r)))
            if not order_by:
                order_by = 'distance'

        if not order_by:
            order_by = '-modified'
        if order_by.endswith('distance'):
            if not origin:
                raise NotImplementedError
            qs = qs.annotate(distance=Distance('lonLat', origin))
        return qs.order_by(order_by)


    def create(self, request, *args, **kwargs):
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
            pp = PostPiece.create_smart(uplace, pb, is_remove=True)


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
            uplace, is_created = UserPlace.get_or_create_smart(pb, vd)

            # valid check
            if not pb.is_valid(uplace):
                raise ValueError('PostPiece 생성을 위한 최소한의 정보도 없음')

            # PostPiece 생성
            pp = PostPiece.create_smart(uplace, pb)

            # 임시적인 어드민 구현을 위해, MAMMA 가 추가로 뽑아준 post 가 있으면 추가로 포스팅
            pb_MAMMA = pb.pb_MAMMA
            if pb_MAMMA:
                # 아래 호출에서 Place 가 생성되고, 필요시 Place PostPiece 도 생성됨
                # TODO : 좀 더 Readability 가 높은 형태로 리팩토링
                uplace, is_created = UserPlace.get_or_create_smart(pb_MAMMA, vd)

            # Place.lonLat 관련 예외 처리
            lonLat = (pb_MAMMA and pb_MAMMA.lonLat) or pb.lonLat
            if lonLat and uplace.place and (not uplace.place.lonLat or (pb_MAMMA and pb_MAMMA.lonLat)):
                uplace.place.lonLat = lonLat
                uplace.place.save()

            # 현재 위치 저장인 경우 이미지에 추가 정보 붙이기
            if is_created and lonLat and pb.images and len(pb.images) == 1 and pb.images[0]:
                img = pb.images[0]
                img.lonLat = lonLat
                img.timestamp = uplace.created - 1000
                img.save()

            # 빠른 장소화를 위한 flag 세팅
            if is_created and not uplace.place:
                uplace.is_hurry2placed = True

            # 최종 저장
            uplace.lonLat = (uplace.place and uplace.place.lonLat) or lonLat or uplace.lonLat
            uplace.modified = get_timestamp()
            # TODO : 아래 코드가 테스트되는 테스트 추가
            uplace.is_drop = False
            uplace.save()

            # Placed by Contents
            if pb.urls:
                placesets = [set(url.places.all()) for url in pb.urls if url.places]
                if placesets:
                    places = list(reduce(lambda a, b: a & b, placesets))
                    for place in places:
                        uplace.process_child(place)


        #######################################
        # 결과 처리
        #######################################
        serializer = self.get_serializer(uplace)
        cache_expire_ru(vd, 'uplaces')
        return Response(serializer.data, status=status.HTTP_201_CREATED)


    def perform_destroy(self, instance):
        # vd 조회
        vd = self.vd
        if not vd:
            raise NotImplementedError

        # 장소화 안된 경우 완전 삭제
        if not instance.place:
            super(UserPlaceViewset, self).perform_destroy(instance)

        # 장소화된 경우 drop 처리
        else:
            instance.is_drop = True
            instance.save()
            pb = PostBase('{"notes": [{"content": "delete"}]}')
            pp = PostPiece.create_smart(instance, pb, is_drop=True)

        # remove cache
        cache_expire_ru(vd, 'uplaces')

    @list_route(methods=['get'])
    def regions(self, request):
        from place.libs import compute_regions
        result = compute_regions(self.vd)
        json = list()
        if result:
            for r in result[:120]:
                lonLat = r.lonLat
                radius = r.radius
                radius_json = int(round(radius + RADIUS_LOCAL_RANGE*2 + 0.499))
                lonLat_json = dict(lon=lonLat.x, lat=lonLat.y)
                m = r.representative_member
                thumbnail = (m.userPost.images and m.userPost.images[0].url_summarized) or\
                            (m.placePost and m.placePost.images and m.placePost.images[0].url_summarized) or None
                json.append(dict(lonLat=lonLat_json, count=r.count, radius=radius_json, thumbnail=thumbnail))
        return Response(json, status=status.HTTP_200_OK)

    @detail_route(methods=['get'])
    def shorten_url(self, request, pk=None):
        uplace = self.get_object()
        result = uplace.make_shorten_url()
        return Response({'shorten_url': uplace.wrapping_shorten_url}, status=status.HTTP_200_OK)

    # TODO : 관련 테스트 추가
    @detail_route(methods=['post'])
    def create_bounded(self, request, pk=None):
        # vd 조회
        vd = self.vd
        if not vd: return Response(status=status.HTTP_401_UNAUTHORIZED)

        uplace = self.get_object()
        pb = PostBase(request.data['add'])
        uplace_temp = UserPlace.objects.create(vd=vd, is_bounded=True, place=uplace.place, lonLat=uplace.lonLat)
        pp = PostPiece.create_smart(uplace_temp, pb)
        serializer = self.get_serializer(uplace_temp)
        cache_expire_ru(vd, 'uplaces')
        return Response(serializer.data, status=status.HTTP_201_CREATED)
