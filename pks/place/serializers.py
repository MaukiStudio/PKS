#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.serializers import ReadOnlyField

from place import models
from base.serializers import BaseSerializer


class PlaceSerializer(BaseSerializer):
    userPost = ReadOnlyField(source='userPost.json')
    placePost = ReadOnlyField(source='placePost.json')
    place_id = ReadOnlyField(source='id')

    class Meta:
        model = models.Place
        exclude = ('id', 'vds',)

    def to_representation(self, instance):
        instance.computePost(self.vd.realOwner_vd_ids)
        return super(PlaceSerializer, self).to_representation(instance)


class PlaceContentSerializer(BaseSerializer):
    class Meta:
        model = models.PlaceContent


class UserPlaceSerializer(BaseSerializer):
    userPost = ReadOnlyField(source='userPost.json')
    placePost = ReadOnlyField(source='placePost.json')
    place_id = ReadOnlyField(source='place.id')
    created = ReadOnlyField()

    class Meta:
        model = models.UserPlace
        exclude = ('id', 'place', 'vd',)
