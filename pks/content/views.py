#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.viewsets import ModelViewSet

from content import models
from content import serializers


class FsVenueViewset(ModelViewSet):
    queryset = models.FsVenue.objects.all()
    serializer_class = serializers.FsVenueSerializer


class NoteViewset(ModelViewSet):
    queryset = models.Note.objects.all()
    serializer_class = serializers.NoteSerializer


class NameViewset(ModelViewSet):
    queryset = models.Name.objects.all()
    serializer_class = serializers.NameSerializer


class AddressViewset(ModelViewSet):
    queryset = models.Address.objects.all()
    serializer_class = serializers.AddressSerializer
