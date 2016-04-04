#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.serializers import ModelSerializer, ReadOnlyField

from place import models


class PlaceField(ReadOnlyField):
    def get_attribute(self, instance):
        instance.computePost([])
        return super(PlaceField, self).get_attribute(instance)


class PlaceSerializer(ModelSerializer):
    placePost = PlaceField()

    class Meta:
        model = models.Place
        exclude = ('vds',)


class PlaceContentSerializer(ModelSerializer):
    class Meta:
        model = models.PlaceContent


class UserPostSerializer(ModelSerializer):
    userPost = ReadOnlyField()
    placePost = ReadOnlyField()

    class Meta:
        model = models.UserPost
        exclude = ('id',)
