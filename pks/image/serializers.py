#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.serializers import ModelSerializer, ReadOnlyField

from image.models import Image, RawFile
from base.serializers import ContentSerializer


class ImageSerializer(ContentSerializer):
    class Meta:
        model = Image
        exclude = ('id', 'dhash',)


class RawFileSerializer(ModelSerializer):
    uuid = ReadOnlyField()

    class Meta:
        model = RawFile
        exclude = ('id', 'mhash',)
