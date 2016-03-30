#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from hashlib import md5
from uuid import UUID
from base64 import b16encode
from django.utils import timezone
from django.contrib.gis.db import models


class Url(models.Model):
    uuid = models.UUIDField(primary_key=True, default=None)
    url = models.URLField(max_length=255, blank=True, null=True, default=None)
    content = models.TextField(blank=True, null=True, default=None)
    lastCrawlDate = models.DateTimeField(blank=True, null=True, default=None)

    def set_uuid(self):
        m = md5()
        m.update(self.url)
        h = m.digest()
        self.uuid = UUID(b16encode(h))
        return self.uuid

    def save(self, *args, **kwargs):
        if self.url and not self.uuid:
            self.set_uuid()
        if self.content:
            self.lastCrawlDate = timezone.now()
        super(Url, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.url
