#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from uuid import UUID
from hashlib import md5
from base64 import b16encode
from django.contrib.gis.db import models


class FsVenue(models.Model):
    uuid = models.UUIDField(primary_key=True, default=None)
    fsVenueId = models.CharField(max_length=255, blank=True, null=True, default=None)

    def __unicode__(self):
        return self.fsVenueId

    def set_uuid(self):
        self.uuid = UUID(self.fsVenueId.rjust(32, b'0'))
        return self.uuid

    def save(self, *args, **kwargs):
        if self.fsVenueId and not self.uuid:
            self.set_uuid()
        super(FsVenue, self).save(*args, **kwargs)


class Note(models.Model):
    uuid = models.UUIDField(primary_key=True, default=None)
    content = models.CharField(max_length=255, blank=True, null=True, default=None)

    def __unicode__(self):
        return self.content

    def set_uuid(self):
        m = md5()
        m.update(self.content.encode(encoding='utf-8'))
        h = m.digest()
        self.uuid = UUID(b16encode(h))
        return self.uuid

    def save(self, *args, **kwargs):
        if self.content and not self.uuid:
            self.set_uuid()
        super(Note, self).save(*args, **kwargs)


class Name(models.Model):
    uuid = models.UUIDField(primary_key=True, default=None)
    content = models.CharField(max_length=255, blank=True, null=True, default=None)

    def __unicode__(self):
        return self.content

    def set_uuid(self):
        m = md5()
        m.update(self.content.encode(encoding='utf-8'))
        h = m.digest()
        self.uuid = UUID(b16encode(h))
        return self.uuid

    def save(self, *args, **kwargs):
        if self.content and not self.uuid:
            self.set_uuid()
        super(Name, self).save(*args, **kwargs)


class Address(models.Model):
    uuid = models.UUIDField(primary_key=True, default=None)
    content = models.CharField(max_length=255, blank=True, null=True, default=None)

    def __unicode__(self):
        return self.content

    def set_uuid(self):
        m = md5()
        m.update(self.content.encode(encoding='utf-8'))
        h = m.digest()
        self.uuid = UUID(b16encode(h))
        return self.uuid

    def save(self, *args, **kwargs):
        if self.content and not self.uuid:
            self.set_uuid()
        super(Address, self).save(*args, **kwargs)
