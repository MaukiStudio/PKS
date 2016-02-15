#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.viewsets import ModelViewSet

from account import models
from account import serializers


class VirtualDeviceViewset(ModelViewSet):
    queryset = models.VirtualDevice.objects.all()
    serializer_class = serializers.VirtualDeviceSerializer