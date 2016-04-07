#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from url import models
from base.serializers import ContentSerializer


class UrlSerializer(ContentSerializer):
    class Meta:
        model = models.Url
        exclude = ('id',)
