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
        exclude = ('id', 'place', 'vd', 'mask', 'uplace_uuid',)

    def to_representation(self, instance):
        vd = self.vd
        if vd:
            base_post = instance.parent and instance.parent.userPost or PostBase()
            base_post.reset_except_region_property()
            instance.computePost(vd.realOwner_publisher_ids, base_post)
        return super(ImportedPlaceSerializer, self).to_representation(instance)
