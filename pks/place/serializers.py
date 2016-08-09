#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.serializers import ReadOnlyField
from django.contrib.gis.geos import GEOSGeometry

from place.models import Place, UserPlace, PostPiece
from base.serializers import BaseSerializer


class PlaceSerializer(BaseSerializer):
    placePost = ReadOnlyField(source='placePost.cjson')
    userPost = ReadOnlyField(source='userPost.cjson')
    place_id = ReadOnlyField(source='id')
    lonLat = ReadOnlyField(source='lonLat_json')

    class Meta:
        model = Place
        exclude = ('id', 'placeName',)

    def to_representation(self, instance):
        vd = self.vd
        if vd:
            instance.computePost(vd.realOwner_vd_ids)
        return super(PlaceSerializer, self).to_representation(instance)


class PostPieceSerializer(BaseSerializer):
    class Meta:
        model = PostPiece


class UserPlaceSerializer(BaseSerializer):
    userPost = ReadOnlyField(source='userPost.cjson')
    placePost = ReadOnlyField(source='placePost.cjson')
    uplace_uuid = ReadOnlyField(source='uuid')
    lonLat = ReadOnlyField(source='lonLat_json')
    place_id = ReadOnlyField()
    created = ReadOnlyField()
    distance_from_origin = ReadOnlyField()
    NLL = ReadOnlyField()
    shorten_url = ReadOnlyField(source='wrapping_shorten_url')

    class Meta:
        model = UserPlace
        exclude = ('id', 'place', 'vd', 'mask',)

    def to_representation(self, instance):
        if 'request' in self._context:
            params = self._context['request'].query_params
            if 'lon' in params and 'lat' in params:
                lon = float(params['lon'])
                lat = float(params['lat'])
                p = GEOSGeometry('POINT(%f %f)' % (lon, lat), srid=4326)
                instance.origin = p
            if 'tags' in params and params['tags']:
                from tag.models import Tag
                tags = Tag.tags_from_param(params['tags'])
                instance.search_tags = tags
        return super(UserPlaceSerializer, self).to_representation(instance)

