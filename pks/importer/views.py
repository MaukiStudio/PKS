#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.response import Response
from rest_framework import status
from json import loads as json_loads

from base.views import BaseViewset
from importer.models import Proxy, Importer, ImportedPlace
from importer.serializers import ProxySerializer, ImporterSerializer, ImportedPlaceSerializer
from account.models import VD


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
        if proxy.vd:
            if proxy.vd == vd:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            if proxy.vd.is_private:
                if not proxy.vd.parent:
                    raise NotImplementedError
                if proxy.vd.parent != vd:
                    return Response(status=status.HTTP_403_FORBIDDEN)

        # importer 생성
        importer, created = Importer.objects.get_or_create(publisher=proxy, subscriber=vd)

        # 결과 처리
        serializer = self.get_serializer(importer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ImportedPlaceViewset(BaseViewset):
    queryset = ImportedPlace.objects.all()
    serializer_class = ImportedPlaceSerializer
