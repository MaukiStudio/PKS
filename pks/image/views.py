#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.viewsets import ModelViewSet

from image import models
from image import serializers


class ImageViewset(ModelViewSet):
    queryset = models.Image.objects.all()
    serializer_class = serializers.ImageSerializer
