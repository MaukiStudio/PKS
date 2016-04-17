#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from content import models
from base.serializers import ContentSerializer


class LegacyPlaceSerializer(ContentSerializer):
    class Meta:
        model = models.LegacyPlace
        exclude = ('id',)


class PhoneNumberSerializer(ContentSerializer):
    class Meta:
        model = models.PhoneNumber
        exclude = ('id',)


class PlaceNameSerializer(ContentSerializer):
    class Meta:
        model = models.PlaceName
        exclude = ('id',)


class AddressSerializer(ContentSerializer):
    class Meta:
        model = models.Address
        exclude = ('id',)


class PlaceNoteSerializer(ContentSerializer):
    class Meta:
        model = models.PlaceNote
        exclude = ('id',)


class ImageNoteSerializer(ContentSerializer):
    class Meta:
        model = models.ImageNote
        exclude = ('id',)

