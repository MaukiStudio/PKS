#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.serializers import ModelSerializer

from url import models


class UrlSerializer(ModelSerializer):

    class Meta:
        model = models.Url
