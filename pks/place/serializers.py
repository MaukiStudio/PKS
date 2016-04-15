#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.serializers import ReadOnlyField

from place.models import Place, UserPlace, PlaceContent, PostPiece
from base.serializers import BaseSerializer


class PlaceSerializer(BaseSerializer):
    placePost = ReadOnlyField(source='placePost.json')
    place_id = ReadOnlyField(source='id')

    class Meta:
        model = Place
        exclude = ('id', 'vds',)


class PlaceContentSerializer(BaseSerializer):
    class Meta:
        model = PlaceContent


class PostPieceSerializer(BaseSerializer):
    class Meta:
        model = PostPiece


class UserPlaceSerializer(BaseSerializer):
    userPost = ReadOnlyField(source='userPost.json')
    placePost = ReadOnlyField(source='placePost.json')
    uplace_uuid = ReadOnlyField(source='uuid')
    place_id = ReadOnlyField()
    created = ReadOnlyField()

    class Meta:
        model = UserPlace
        exclude = ('id', 'place', 'vd',)
