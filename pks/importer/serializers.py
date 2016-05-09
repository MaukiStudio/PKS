#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from base.serializers import BaseSerializer
from importer.models import Proxy, Importer, ImportedPlace
from place.serializers import UserPlaceSerializer


class ProxySerializer(BaseSerializer):
    class Meta:
        model = Proxy


class ImporterSerializer(BaseSerializer):
    class Meta:
        model = Importer


class ImportedPlaceSerializer(UserPlaceSerializer):
    class Meta:
        model = ImportedPlace
        exclude = ('id', 'place', 'vd',)
