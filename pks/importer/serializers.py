#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from base.serializers import BaseSerializer, ReadOnlyField
from importer.models import Proxy, Importer, ImportedPlace


class ProxySerializer(BaseSerializer):
    class Meta:
        model = Proxy


class ImporterSerializer(BaseSerializer):
    class Meta:
        model = Importer


class ImportedPlaceSerializer(BaseSerializer):
    userPost = ReadOnlyField(source='userPost.json')
    placePost = ReadOnlyField(source='placePost.json')
    iplace_uuid = ReadOnlyField(source='uuid')
    lonLat = ReadOnlyField(source='lonLat_json')
    place_id = ReadOnlyField()

    class Meta:
        model = ImportedPlace
        exclude = ('id', 'place', 'vd', 'modified',)
