#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from base64 import b16encode
from django.contrib.gis.db import models


class Image(models.Model):
    uuid = models.UUIDField(primary_key=True, default=None)
    file = models.ImageField(blank=True, null=True, default=None)

    def __str__(self):
        return '%s.jpg' % b16encode(self.uuid.bytes)

