#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.serializers import ModelSerializer

from url import models


class UrlSerializer(ModelSerializer):

    class Meta:
        model = models.Url

    def create(self, validated_data):
        url = models.Url(**validated_data)
        uuid = url.set_uuid()
        url.save()
        return url
