#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from hashlib import md5
from uuid import UUID
from base64 import b16encode
from django.contrib.gis.db import models


class Url(models.Model):
    id = models.UUIDField(primary_key=True, default=None)
    content = models.URLField(max_length=255, blank=True, null=True, default=None)

    def set_id(self):
        m = md5()
        m.update(self.content)
        h = m.digest()
        self.id = UUID(b16encode(h))

    def save(self, *args, **kwargs):
        if self.content and not self.id:
            self.set_id()
        super(Url, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.content

    @property
    def uuid(self):
        return '%s.url' % b16encode(self.id.bytes)
