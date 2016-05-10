#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.response import Response
from rest_framework import status
from json import loads as json_loads
from rest_framework.decorators import detail_route

from base.views import BaseViewset
from importer.models import Proxy, Importer, ImportedPlace
from importer.serializers import ProxySerializer, ImporterSerializer, ImportedPlaceSerializer
from account.models import VD
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

        # check validation
        if not proxy.vd:
            raise NotImplementedError
        if proxy.vd == vd:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if proxy.vd.is_private:
            if not proxy.vd.parent:
                raise NotImplementedError
            if proxy.vd.parent != vd:
                return Response(status=status.HTTP_403_FORBIDDEN)

        # importer 생성
        importer, is_created = Importer.objects.get_or_create(publisher=proxy, subscriber=vd)

        # 결과 처리
        serializer = self.get_serializer(importer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ImportedPlaceViewset(BaseViewset):
    queryset = ImportedPlace.objects.all()
    serializer_class = ImportedPlaceSerializer

    def get_queryset(self):
        params = self.request.query_params
        if 'ru' in params and params['ru'] != 'myself':
            # Now, ru=myself only
            raise NotImplementedError
        publisher_ids = self.publisher_ids
        if publisher_ids:
            qs1 = self.queryset.filter(vd_id__in=publisher_ids)
            qs2 = qs1.exclude(place_id=None)
            qs3 = qs2.exclude(place_id__in=self.subscriber_places)
            return qs3.order_by('-modified')
        else:
            return self.queryset.filter(id=None)

    # TODO : 캐싱 처리에 용이하도록 리팩토링 및 캐싱
    @property
    def publisher_ids(self):
        importers = Importer.objects.filter(subscriber_id__in=self.vd.realOwner_vd_ids)
        return [importer.publisher_id for importer in importers]

    # TODO : 튜닝
    @property
    def subscriber_places(self):
        places = Place.objects.filter(uplaces__vd_id__in=self.vd.realOwner_vd_ids)
        return places

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
        # 일단 take 시점의 iplace.userPost 를 복사함
        # TODO : 향후 iplace.userPost 변경 사항을 반영하는 최신화가 필요할 수도...
        pb = PostBase()
        pb.iplace_uuid = iplace.uuid
        pb.place_id = iplace.place_id
        pb.uplace_uuid = None

        uplace, is_created = UserPlace.get_or_create_smart(pb, vd)
        pp = PostPiece.objects.create(place=None, uplace=uplace, vd=vd, data=pb.json)
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
            pp = PostPiece.objects.create(is_drop=True, place=None, uplace=uplace, vd=vd, data=pb.json)
            uplace.is_drop = True
            uplace.save()
            serializer = UserPlaceSerializer(uplace)
            return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)
        else:
            # 매칭되는 UserPlace 가 있었다면 무시
            # 이를 drop 처리하려면 delete /uplaces/detail/
            serializer = UserPlaceSerializer(uplace)
            return Response(serializer.data, status=status.HTTP_200_OK)
