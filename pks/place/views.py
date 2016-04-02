#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from json import loads as json_loads
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status

from place import models
from place import serializers
from account.models import VD
from pks.settings import VD_SESSION_KEY


class PlaceViewset(ModelViewSet):
    queryset = models.Place.objects.all()
    serializer_class = serializers.PlaceSerializer


class PlaceContentViewset(ModelViewSet):
    queryset = models.PlaceContent.objects.all()
    serializer_class = serializers.PlaceContentSerializer


class UserPostViewset(ModelViewSet):
    queryset = models.UserPost.objects.all()
    serializer_class = serializers.UserPostSerializer

    def create(self, request, *args, **kwargs):
        vd_id = request.session[VD_SESSION_KEY]
        add = json_loads(request.data['add'])
        place_id = add['place_id']

        vd = VD.objects.get(id=vd_id)
        place = models.Place.objects.get(id=place_id)
        post, created = models.UserPost.objects.get_or_create(vd=vd, place=place)

        serializer = self.get_serializer(post)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
