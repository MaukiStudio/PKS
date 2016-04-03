#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.serializers import ModelSerializer, ReadOnlyField

from place import models


class PlaceSerializer(ModelSerializer):
    class Meta:
        model = models.Place


class PlaceContentSerializer(ModelSerializer):
    class Meta:
        model = models.PlaceContent


class UserPostSerializer(ModelSerializer):
    userPost = ReadOnlyField()
    placePost = ReadOnlyField(source='place.placePost')

    class Meta:
        model = models.UserPost
        exclude = ('vd', 'place',)
