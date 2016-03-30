#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from uuid import UUID
from random import randrange
from django.contrib.gis.db import models

from account.models import VD
from image.models import Image
from url.models import Url
from content.models import FsVenue, Note, Name, Address
from delorean import Delorean


class Place(models.Model):
    pass


class PlaceContent(models.Model):
    # uuid
    uuid = models.UUIDField(primary_key=True, default=None)

    # References
    place = models.ForeignKey(Place, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')
    vd = models.ForeignKey(VD, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')

    # Contents
    lonLat = models.PointField(blank=True, null=True, default=None)
    image = models.ForeignKey(Image, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')
    url = models.ForeignKey(Url, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')
    fsVenue = models.ForeignKey(FsVenue, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')
    note = models.ForeignKey(Note, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')
    name = models.ForeignKey(Name, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')
    addr = models.ForeignKey(Address, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')

    def set_uuid(self):
        timestamp = Delorean().epoch
        vd_pk = (self.vd and self.vd.pk) or 0
        hstr = hex((int(round(timestamp*1000)) << 8*8) | (vd_pk << 2*8) | randrange(0, 65536))[2:-1]
        self.uuid = UUID(hstr.rjust(32, b'0'))
        return self.uuid

    def save(self, *args, **kwargs):
        if not self.uuid:
            self.set_uuid()
        super(PlaceContent, self).save(*args, **kwargs)
