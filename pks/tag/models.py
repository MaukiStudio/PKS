#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.gis.db import models

from place.models import UserPlace, Place


class Tag(models.Model):
    name = models.CharField(max_length=254, blank=True, null=True, default=None)
    uplaces = models.ManyToManyField(UserPlace, through='UserPlaceTag', related_name='tags')
    places = models.ManyToManyField(Place, through='PlaceTag', related_name='tags')

    def __unicode__(self):
        return self.name


class UserPlaceTag(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='uptags')
    uplace = models.ForeignKey(UserPlace, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='uptags')
    created = models.BigIntegerField(blank=True, null=True, default=None)

    def __unicode__(self):
        return self.tag and self.tag.name or None


class PlaceTag(models.Model):
    tag = models.ForeignKey(Tag, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='ptags')
    place = models.ForeignKey(Place, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='ptags')
    created = models.BigIntegerField(blank=True, null=True, default=None)
    prob = models.FloatField(blank=True, null=True, default=None)

    def __unicode__(self):
        return self.tag and self.tag.name or None
