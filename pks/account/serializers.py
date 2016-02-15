#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.serializers import HyperlinkedModelSerializer

from account import models


class VirtualDeviceSerializer(HyperlinkedModelSerializer):
    class Meta:
        model = models.VirtualDevice
        fields = ('url',)