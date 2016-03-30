#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.gis.db import models

from account.models import VD
from image.models import Image
from url.models import Url
from content.models import FsVenue, Note, Name, Address


class Place(models.Model):
    pass


class PlaceContent(models.Model):
    # References
    place = models.ForeignKey(Place, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')
    vd = models.ForeignKey(VD, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')

    # Contents
    lonLat = models.PointField(blank=True, null=True, default=None)
    image = models.ForeignKey(Image, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')
    url = models.ForeignKey(Url, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')
    fsVenue = models.ForeignKey(FsVenue, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')
    note = models.ForeignKey(Note, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')
    name = models.ForeignKey(Name, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')
    addr = models.ForeignKey(Address, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')

    def save(self, *args, **kwargs):
        super(PlaceContent, self).save(*args, **kwargs)
