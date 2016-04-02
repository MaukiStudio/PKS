#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from json import loads as json_loads
from rest_framework.viewsets import ModelViewSet

from place import models
from place import serializers
from rest_framework.decorators import list_route


class PlaceViewset(ModelViewSet):
    queryset = models.Place.objects.all()
    serializer_class = serializers.PlaceSerializer

    @list_route(methods=['post'])
    def post(self, request):
        myPost = json_loads(request.data['myPost'])
        return None


class PlaceContentViewset(ModelViewSet):
    queryset = models.PlaceContent.objects.all()
    serializer_class = serializers.PlaceContentSerializer
