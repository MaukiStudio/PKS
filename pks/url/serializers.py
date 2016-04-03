#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.serializers import ModelSerializer, ReadOnlyField

from url import models
from base.utils import HashCollisionError


class UrlSerializer(ModelSerializer):
    uuid = ReadOnlyField()

    class Meta:
        model = models.Url
        exclude = ('id',)

    def create(self, validated_data):
        url, created = models.Url.objects.get_or_create(**validated_data)
        if url.content != validated_data['content']:
            raise HashCollisionError
        return url
