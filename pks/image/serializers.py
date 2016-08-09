#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.serializers import ModelSerializer, ReadOnlyField

from image.models import Image, RawFile
from base.serializers import ContentSerializer


class ImageSerializer(ContentSerializer):
    class Meta:
        model = Image
        exclude = ('id', 'phash',)


class RawFileSerializer(ModelSerializer):
    uuid = ReadOnlyField()
    url = ReadOnlyField()

    class Meta:
        model = RawFile
        exclude = ('id', 'mhash',)
        extra_kwargs = {'file': {'write_only': True}}
