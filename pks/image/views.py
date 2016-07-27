#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.response import Response
from rest_framework import status
from django.contrib.gis.geos import GEOSGeometry
from datetime import datetime

from image.models import Image, RawFile
from image.serializers import ImageSerializer, RawFileSerializer
from base.views import BaseViewset, ContentViewset
from delorean import Delorean


class ImageViewset(ContentViewset):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer
    http_method_names = ['get', 'post', 'patch']

    def create(self, request, *args, **kwargs):
        if 'content' not in request.data or not request.data['content']:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        img, is_created = Image.get_or_create_smart(request.data['content'])
        dirty = False
        if 'lon' in request.data and request.data['lon'] and 'lat' in request.data and request.data['lat']:
            lon = float(request.data['lon'])
            lat = float(request.data['lat'])
            point = GEOSGeometry('POINT(%f %f)' % (lon, lat), srid=4326)
            img.lonLat = point
            dirty = True
        if 'local_datetime' in request.data and request.data['local_datetime']:
            dt = datetime.strptime(request.data['local_datetime'], '%Y:%m:%d %H:%M:%S')
            # TODO : VD.timezone 을 참조하여 변환
            d = Delorean(dt, timezone='Asia/Seoul')
            img.timestamp = int(round(d.epoch*1000))
            dirty = True
        if dirty:
            img.save()

        serializer = self.get_serializer(img)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class RawFileViewset(BaseViewset):
    queryset = RawFile.objects.all()
    serializer_class = RawFileSerializer

    def perform_create(self, serializer):
        rf = serializer.save(vd=self.vd)
        # post_save : celery task
        rf.start()
