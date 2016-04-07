#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from content import models
from content import serializers
from base.views import ContentViewset


class LegacyPlaceViewset(ContentViewset):
    queryset = models.LegacyPlace.objects.all()
    serializer_class = serializers.LegacyPlaceSerializer


class ShortTextViewset(ContentViewset):
    queryset = models.ShortText.objects.all()
    serializer_class = serializers.ShortTextSerializer


class PhoneNumberViewset(ContentViewset):
    queryset = models.PhoneNumber.objects.all()
    serializer_class = serializers.PhoneNumberSerializer

