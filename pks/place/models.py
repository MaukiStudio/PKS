#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from uuid import UUID
from random import randrange
from django.contrib.gis.db import models

from account.models import VD
from image.models import Image
from url.models import Url
from content.models import FsVenue, ShortText
from delorean import Delorean


class Place(models.Model):
    post_cache = None

    @property
    def post(self):
        if self.post_cache:
            return self.post_cache
        result = dict(id=self.id, latitude=None, longitude=None, images=list(), urls=list(), fsVenue=None, notes=list(), name=None, addr=None,)
        for pc in self.pcs.all().order_by('-uuid'):
            if pc.lonLat and not result['latitude']: result['latitude'] = pc.lonLat.y
            if pc.lonLat and not result['longitude']: result['longitude'] = pc.lonLat.x
            if pc.image: result['images'].append(pc.image.file.url)
            if pc.url: result['urls'].append(pc.url.url)
            if pc.fsVenue and not result['fsVenue']: result['fsVenue'] = pc.fsVenue.fsVenueId
            if pc.note: result['notes'].append(pc.note.content)
            if pc.name and not result['name']: result['name'] = pc.name.content
            if pc.addr and not result['addr']: result['addr'] = pc.addr.content
        self.post_cache = result
        return self.post_cache


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
    stext = models.ForeignKey(ShortText, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')

    def set_uuid(self):
        timestamp = int(round(Delorean().epoch*1000))
        vd_pk = (self.vd and self.vd.pk) or 0
        hstr = hex((1 << 16*8-2) | (timestamp << 8*8-2) | (vd_pk << 2*8-2) | randrange(0, 65536/4))[2:-1]
        self.uuid = UUID(hstr.rjust(32, b'0'))
        return self.uuid

    def save(self, *args, **kwargs):
        if not self.uuid:
            self.set_uuid()
        super(PlaceContent, self).save(*args, **kwargs)
