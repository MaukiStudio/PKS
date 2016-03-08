#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.decorators import list_route

from account import models
from account import serializers


class UserViewset(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = serializers.UserSerializer

    '''
    @list_route(methods=['post'])
    def register(self, request):
        pass
    '''

class VDViewset(ModelViewSet):
    queryset = models.VD.objects.all()
    serializer_class = serializers.VDSerializer