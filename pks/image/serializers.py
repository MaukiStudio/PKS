#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import IntegrityError
from rest_framework.serializers import ModelSerializer

from image import models


class ImageSerializer(ModelSerializer):

    class Meta:
        model = models.Image
        read_only_fields = ('uuid',)

    def create(self, validated_data):
        img = models.Image(**validated_data)
        uuid = img.set_uuid()

        # TODO : 문제가 있는 구현. 향후 개선해야 함
        try:
            result = models.Image.objects.get(pk=uuid)
        except models.Image.DoesNotExist:
            img.save()
            result = img
        return result
