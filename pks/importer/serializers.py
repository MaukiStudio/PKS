#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from base.serializers import BaseSerializer, ReadOnlyField
from importer.models import Proxy, Importer, ImportedPlace
from place.serializers import UserPlaceSerializer
from place.models import PostBase


class ProxySerializer(BaseSerializer):
    class Meta:
        model = Proxy


class ImporterSerializer(BaseSerializer):
    class Meta:
        model = Importer


class ImportedPlaceSerializer(UserPlaceSerializer):
    iplace_uuid = ReadOnlyField(source='uuid')

    class Meta:
        model = ImportedPlace
        exclude = ('id', 'place', 'vd', 'mask', 'uplace_uuid', 'shorten_url',)

    def to_representation(self, instance):
        vd = self.vd
        if vd:
            instance.subscriber = vd
        return super(ImportedPlaceSerializer, self).to_representation(instance)
