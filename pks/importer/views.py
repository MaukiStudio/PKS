#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.response import Response
from rest_framework import status
from json import loads as json_loads
from rest_framework.decorators import detail_route
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance
from django.db.models import F

from base.views import BaseViewset
from importer.models import Proxy, Importer, ImportedPlace
from importer.serializers import ProxySerializer, ImporterSerializer, ImportedPlaceSerializer
from account.models import VD, RealUser
from place.models import Place, UserPlace, PostPiece
from place.post import PostBase
from place.serializers import UserPlaceSerializer


class ProxyViewset(BaseViewset):
    queryset = Proxy.objects.all()
    serializer_class = ProxySerializer


class ImporterViewset(BaseViewset):
    queryset = Importer.objects.all()
    serializer_class = ImporterSerializer

    def create(self, request, *args, **kwargs):
        # vd 조회
        vd = self.vd
        if not vd: return Response(status=status.HTTP_401_UNAUTHORIZED)

        # guide 조회
        guide = request.data['guide']
        if type(guide) is not dict:
            guide = json_loads(guide)

        # myself 변환
        if 'vd' in guide and guide['vd'] == 'myself':
            guide['vd'] = vd.id

        # check validation 1
        if 'type' in guide and guide['type'] == 'user':
            ru = RealUser.objects.get(email=guide['email'])
            if ru == self.vd.realOwner:
                return Response(status=status.HTTP_400_BAD_REQUEST)

        # proxy 조회
        try:
            proxy = Proxy.objects.get(guide=guide)
        except Proxy.DoesNotExist:
            vd_publisher = VD()
            # TODO : type 이 images 가 아닌 경우에 대한 구현
            if guide['type'] == 'images':
                vd_publisher.is_private = True
                vd_publisher.is_public = False
                vd_publisher.parent = vd
            vd_publisher.save()
            proxy = Proxy.objects.create(vd=vd_publisher, guide=guide)

        # check validation 2
        if not proxy.vd:
            raise NotImplementedError
        if proxy.vd == vd:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if proxy.vd.is_private:
            if not proxy.vd.parent:
                raise NotImplementedError
            if proxy.vd.parent != vd:
                return Response(status=status.HTTP_403_FORBIDDEN)

        # importer 생성 및 celery task 처리
        importer, is_created = Importer.objects.get_or_create(publisher=proxy, subscriber=vd)
        importer.start(high_priority=is_created)

        # 결과 처리
        serializer = self.get_serializer(importer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# TODO : UserPlaceViewset 과 유사/중복존재. 가능할 때 리팩토링
class ImportedPlaceViewset(BaseViewset):
    queryset = ImportedPlace.objects.all()
    serializer_class = ImportedPlaceSerializer

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

        vd_ids = self.vd.realOwner_publisher_ids
        qs = self.queryset.filter(vd_id__in=vd_ids)
        qs = qs.exclude(id__in=self.vd.realOwner_duplicated_iplace_ids)
        qs = qs.filter(mask=F('mask').bitand(~1))

        # iplace filtering
        qs = qs.exclude(place_id=None)
        qs = qs.exclude(place_id__in=self.vd.realOwner_places)

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


    # ImportedPlace 는 직접 생성할 수 없음. Publisher 에서 생성된 것이 Import 되면서 생성
    def create(self, request, *args, **kwargs):
        return Response(status=status.HTTP_400_BAD_REQUEST)

    # ImportedPlace 는 직접 수정할 수 없음. Publisher 에서 수정하거나 UserPlace 로 전환 후 수정 가능
    def update(self, request, *args, **kwargs):
        return Response(status=status.HTTP_400_BAD_REQUEST)

    @detail_route(methods=['post'])
    def take(self, request, pk=None):
        # vd 조회
        vd = self.vd
        if not vd: return Response(status=status.HTTP_401_UNAUTHORIZED)

        iplace = self.get_object()
        pb = PostBase()
        pb.iplace_uuid = iplace.uuid
        pb.place_id = iplace.place_id
        pb.uplace_uuid = None

        uplace, is_created = UserPlace.get_or_create_smart(pb, vd)
        pp = PostPiece.create_smart(uplace, pb)
        serializer = UserPlaceSerializer(uplace)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @detail_route(methods=['post'])
    def drop(self, request, pk=None):
        # vd 조회
        vd = self.vd
        if not vd: return Response(status=status.HTTP_401_UNAUTHORIZED)

        iplace = self.get_object()
        pb = PostBase()
        pb.iplace_uuid = iplace.uuid
        pb.place_id = iplace.place_id
        pb.uplace_uuid = None

        uplace, is_created = UserPlace.get_or_create_smart(pb, vd)
        if is_created:
            # 매칭되는 UserPlace 가 없었다면 drop 처리
            pp = PostPiece.create_smart(uplace, pb, is_drop=True)
            uplace.is_drop = True
            uplace.save()
            serializer = UserPlaceSerializer(uplace)
            return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)
        else:
            # 매칭되는 UserPlace 가 있었다면 무시
            # 이를 drop 처리하려면 delete /uplaces/detail/
            serializer = UserPlaceSerializer(uplace)
            return Response(serializer.data, status=status.HTTP_200_OK)
