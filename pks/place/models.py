#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.gis.db import models

from account.models import VD
from image.models import Image


class Place(models.Model):
    pass


class PlaceContent(models.Model):
    place = models.ForeignKey(Place, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')
    vd = models.ForeignKey(VD, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')

    image = models.ForeignKey(Image, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')
    lonLat = models.PointField(blank=True, null=True, default=None)

    def save(self, *args, **kwargs):
        if not self.lonLat and self.image and self.image.lonLat:
            self.lonLat = self.image.lonLat
        super(PlaceContent, self).save(*args, **kwargs)
