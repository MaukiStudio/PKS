#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User

from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from account import models
from account import serializers


class UserViewset(ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer

class VirtualDeviceViewset(ModelViewSet):
    queryset = models.VirtualDevice.objects.all()
    serializer_class = serializers.VirtualDeviceSerializer