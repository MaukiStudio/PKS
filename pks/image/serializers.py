#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import IntegrityError
from rest_framework.serializers import ModelSerializer, ReadOnlyField

from image import models


class ImageSerializer(ModelSerializer):
    uuid = ReadOnlyField()

    class Meta:
        model = models.Image
        read_only_fields = ('id', 'exif',)

    def create(self, validated_data):
        img = models.Image(**validated_data)
        img.set_id()

        # TODO : 문제가 있는 구현. 향후 개선해야 함
        try:
            result = models.Image.objects.get(id=img.id)
        except models.Image.DoesNotExist:
            img.save()
            result = img
        return result


class RawFileSerializer(ModelSerializer):
    uuid = ReadOnlyField()

    class Meta:
        model = models.RawFile
        read_only_fields = ('id',)
        exclude = ('mhash',)
