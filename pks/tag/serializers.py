#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from base.serializers import BaseSerializer
from tag.models import Tag, UserPlaceTag, PlaceTag


class TagSerializer(BaseSerializer):
    class Meta:
        model = Tag


class UserPlaceTagSerializer(BaseSerializer):
    class Meta:
        model = UserPlaceTag


class PlaceTagSerializer(BaseSerializer):
    class Meta:
        model = PlaceTag
