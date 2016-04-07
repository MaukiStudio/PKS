#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from url import models
from url import serializers
from base.views import ContentViewset


class UrlViewset(ContentViewset):
    queryset = models.Url.objects.all()
    serializer_class = serializers.UrlSerializer
