#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.serializers import ReadOnlyField
from django.contrib.gis.geos import GEOSGeometry

from place.models import Place, UserPlace, PostPiece
from base.serializers import BaseSerializer


class PlaceSerializer(BaseSerializer):
    placePost = ReadOnlyField(source='placePost.json')
    place_id = ReadOnlyField(source='id')
    lonLat = ReadOnlyField(source='lonLat_json')

    class Meta:
        model = Place
        exclude = ('id', 'placeName',)


class PostPieceSerializer(BaseSerializer):
    class Meta:
        model = PostPiece


class UserPlaceSerializer(BaseSerializer):
    userPost = ReadOnlyField(source='userPost.json')
    placePost = ReadOnlyField(source='placePost.json')
    uplace_uuid = ReadOnlyField(source='uuid')
    lonLat = ReadOnlyField(source='lonLat_json')
    place_id = ReadOnlyField()
    created = ReadOnlyField()
    distance_from_origin = ReadOnlyField()

    class Meta:
        model = UserPlace
        exclude = ('id', 'place', 'vd', 'mask',)

    def to_representation(self, instance):
        params = self._context['request'].query_params
        if 'lon' in params and 'lat' in params:
            lon = float(params['lon'])
            lat = float(params['lat'])
            p = GEOSGeometry('POINT(%f %f)' % (lon, lat), srid=4326)
            instance.origin = p
        return super(UserPlaceSerializer, self).to_representation(instance)
