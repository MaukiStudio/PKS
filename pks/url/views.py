#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.viewsets import ModelViewSet

from url import models
from url import serializers


class UrlViewset(ModelViewSet):
    queryset = models.Url.objects.all()
    serializer_class = serializers.UrlSerializer
