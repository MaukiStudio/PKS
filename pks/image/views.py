#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.viewsets import ModelViewSet

from image import models
from image import serializers
from base.views import BaseViewset


class ImageViewset(ModelViewSet):
    queryset = models.Image.objects.all()
    serializer_class = serializers.ImageSerializer


class RawFileViewset(BaseViewset):
    queryset = models.RawFile.objects.all()
    serializer_class = serializers.RawFileSerializer

    def perform_create(self, serializer):
        serializer.save(vd=self.vd)
