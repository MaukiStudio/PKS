#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from base.views import BaseViewset
from tag.models import Tag, UserPlaceTag, PlaceTag
from tag.serializers import TagSerializer, UserPlaceTagSerializer, PlaceTagSerializer


class TagViewset(BaseViewset):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class UserPlaceTagViewset(BaseViewset):
    queryset = UserPlaceTag.objects.all()
    serializer_class = UserPlaceTagSerializer


class PlaceTagViewset(BaseViewset):
    queryset = PlaceTag.objects.all()
    serializer_class = PlaceTagSerializer
