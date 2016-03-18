#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.gis.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.auth.models import User


class RealUser(models.Model):
    email = models.EmailField(unique=True, blank=False, null=False, default=None)

    def __str__(self):
        return self.email


class VD(models.Model):
    authOwner = models.ForeignKey(User, on_delete=models.SET_DEFAULT, null=True, default=None)
    realOwner = models.ForeignKey(RealUser, on_delete=models.SET_DEFAULT, null=True, default=None)

    lastLonLat = models.PointField(blank=True, null=True, default=None)
    data = JSONField(blank=True, null=True, default=None)

    deviceName = models.CharField(max_length=36, blank=True, null=True, default=None)
    deviceTypeName = models.CharField(max_length=36, blank=True, null=True, default=None)

    def __str__(self):
        email = (self.realOwner and self.realOwner.email) or (self.authOwner and self.authOwner.email) or 'unknown@email'
        deviceTypeName = self.deviceTypeName or 'unknown device'
        deviceNameCaption = (self.deviceName and ' (%s)' % self.deviceName) or ''
        return '%s\'s %s%s' % (email, deviceTypeName, deviceNameCaption)