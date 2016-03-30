#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework.serializers import ModelSerializer

from content import models


class FsVenueSerializer(ModelSerializer):

    class Meta:
        model = models.FsVenue

    def create(self, validated_data):
        fs = models.FsVenue(**validated_data)
        fs.save()
        return fs


class NoteSerializer(ModelSerializer):

    class Meta:
        model = models.Note

    def create(self, validated_data):
        nt = models.Note(**validated_data)
        nt.save()
        return nt


class NameSerializer(ModelSerializer):

    class Meta:
        model = models.Name

    def create(self, validated_data):
        name = models.Name(**validated_data)
        name.save()
        return name


class AddressSerializer(ModelSerializer):

    class Meta:
        model = models.Address

    def create(self, validated_data):
        addr = models.Address(**validated_data)
        addr.save()
        return addr

