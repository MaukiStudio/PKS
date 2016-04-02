#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from uuid import UUID
from hashlib import md5
from base64 import b16encode
from django.contrib.gis.db import models


class FsVenue(models.Model):
    id = models.UUIDField(primary_key=True, default=None)
    content = models.CharField(max_length=255, blank=True, null=True, default=None)

    def __unicode__(self):
        return self.content

    @property
    def uuid(self):
        return '%s.fsv' % self.content

    def set_id(self):
        self.id = UUID(self.content.rjust(32, b'0'))

    def save(self, *args, **kwargs):
        if not self.id and self.content:
            self.set_id()
        super(FsVenue, self).save(*args, **kwargs)


class ShortText(models.Model):
    id = models.UUIDField(primary_key=True, default=None)
    content = models.CharField(max_length=255, blank=True, null=True, default=None)

    def __unicode__(self):
        return self.content

    @property
    def uuid(self):
        return '%s.stxt' % b16encode(self.id.bytes)

    def set_id(self):
        m = md5()
        m.update(self.content.encode(encoding='utf-8'))
        h = m.digest()
        self.id = UUID(b16encode(h))

    def save(self, *args, **kwargs):
        if self.content and not self.id:
            self.set_id()
        super(ShortText, self).save(*args, **kwargs)
