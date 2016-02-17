#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User


class VD(models.Model):
    name = models.CharField(max_length=36, blank=True, null=True, default=None)
    user = models.OneToOneField(User, on_delete=models.SET_DEFAULT, null=True, default=None)
