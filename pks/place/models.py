#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.gis.db import models

from account.models import VD


class Place(models.Model):
    pass


class PlaceContent(models.Model):
    place = models.ForeignKey(Place, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')
    vd = models.ForeignKey(VD, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')
