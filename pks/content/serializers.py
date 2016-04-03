#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.serializers import ModelSerializer, ReadOnlyField

from content import models
from base.utils import HashCollisionError


class FsVenueSerializer(ModelSerializer):
    uuid = ReadOnlyField()

    class Meta:
        model = models.FsVenue
        exclude = ('id',)

    def create(self, validated_data):
        fs, created = models.FsVenue.objects.get_or_create(**validated_data)
        if fs.content != validated_data['content']:
            raise HashCollisionError
        return fs


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
