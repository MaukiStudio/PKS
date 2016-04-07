#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.serializers import ModelSerializer, ReadOnlyField


class ContentSerializer(ModelSerializer):
    uuid = ReadOnlyField()
