#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.serializers import ModelSerializer

from content import models


class FsVenueSerializer(ModelSerializer):

    class Meta:
        model = models.FsVenue

    def create(self, validated_data):
        fs = models.FsVenue(**validated_data)
        fs.save()
        return fs


class ShortTextSerializer(ModelSerializer):

    class Meta:
        model = models.ShortText

    def create(self, validated_data):
        stext = models.ShortText(**validated_data)
        stext.save()
        return stext
