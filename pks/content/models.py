#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from uuid import UUID
from django.contrib.gis.db import models


class FsVenue(models.Model):
    uuid = models.UUIDField(primary_key=True, default=None)
    fsVenueId = models.CharField(max_length=64, blank=True, null=True, default=None)

    def __str__(self):
        return self.fsVenueId

    def set_uuid(self):
        c = len(self.fsVenueId)
        pad = '0'*32
        self.uuid = UUID(pad[c:]+self.fsVenueId)
        return self.uuid

    def save(self, *args, **kwargs):
        if self.fsVenueId and not self.uuid:
            self.set_uuid()
        super(FsVenue, self).save(*args, **kwargs)
