#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.serializers import ModelSerializer, ReadOnlyField

from content import models
from base.utils import HashCollisionError


class LegacyPlaceSerializer(ModelSerializer):
    uuid = ReadOnlyField()

    class Meta:
        model = models.LegacyPlace
        exclude = ('id',)

    def create(self, validated_data):
        lp, created = models.LegacyPlace.objects.get_or_create(**validated_data)
        if lp.content != validated_data['content']:
            raise HashCollisionError
        return lp


class ShortTextSerializer(ModelSerializer):
    uuid = ReadOnlyField()

    class Meta:
        model = models.ShortText
        exclude = ('id',)

    def create(self, validated_data):
        stxt, created = models.ShortText.objects.get_or_create(**validated_data)
        if stxt.content != validated_data['content']:
            raise HashCollisionError
        return stxt
