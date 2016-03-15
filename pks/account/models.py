#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.postgres.fields import JSONField
from django.contrib.auth.models import User


class VD(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_DEFAULT, null=True, default=None)
    deviceName = models.CharField(max_length=36, blank=True, null=True, default=None)
    deviceTypeName = models.CharField(max_length=36, blank=True, null=True, default=None)
    data = JSONField(blank=True, null=True, default=None)
