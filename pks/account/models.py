#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.auth.models import User


class RealUser(models.Model):
    email = models.EmailField(blank=True, null=True, default=None)


class VD(models.Model):
    owner = models.ForeignKey(User, on_delete=models.SET_DEFAULT, null=True, default=None)
    lastLonLat = models.PointField(blank=True, null=True, default=None)
    deviceName = models.CharField(max_length=36, blank=True, null=True, default=None)
    deviceTypeName = models.CharField(max_length=36, blank=True, null=True, default=None)
    data = JSONField(blank=True, null=True, default=None)
