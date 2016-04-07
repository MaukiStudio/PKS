#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from content import models
from base.serializers import ContentSerializer


class LegacyPlaceSerializer(ContentSerializer):
    class Meta:
        model = models.LegacyPlace
        exclude = ('id',)


class ShortTextSerializer(ContentSerializer):
    class Meta:
        model = models.ShortText
        exclude = ('id',)


class PhoneNumberSerializer(ContentSerializer):
    class Meta:
        model = models.PhoneNumber
        exclude = ('id',)
