#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.serializers import ModelSerializer

from place import models


class PlaceSerializer(ModelSerializer):
    class Meta:
        model = models.Place


class PlaceContentSerializer(ModelSerializer):
    class Meta:
        model = models.PlaceContent
