#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.serializers import ModelSerializer, ReadOnlyField

from place import models


class PlaceField(ReadOnlyField):
    def get_attribute(self, instance):
        instance.computePost([])
        return super(PlaceField, self).get_attribute(instance)


class PlaceSerializer(ModelSerializer):
    placePost = PlaceField(source='placePost.json')

    class Meta:
        model = models.Place
        exclude = ('vds',)


class PlaceContentSerializer(ModelSerializer):
    class Meta:
        model = models.PlaceContent


class UserPlaceSerializer(ModelSerializer):
    userPost = ReadOnlyField(source='userPost.json')
    placePost = ReadOnlyField(source='placePost.json')

    class Meta:
        model = models.UserPlace
        exclude = ('id', 'place', 'vd',)
