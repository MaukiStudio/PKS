#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.viewsets import ModelViewSet

from content import models
from content import serializers


class FsVenueViewset(ModelViewSet):
    queryset = models.FsVenue.objects.all()
    serializer_class = serializers.FsVenueSerializer
