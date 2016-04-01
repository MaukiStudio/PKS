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

# stext_type
STEXT_TYPE_PLACE_NOTE = 1
STEXT_TYPE_PLACE_NAME = 2
STEXT_TYPE_ADDRESS = 3
STEXT_TYPE_IMAGE_NOTE = 4


class Place(models.Model):
    @property
    def post(self):
        result = dict(id=self.id, lonLat=None, images=None, urls=list(), fsVenue=None, notes=list(), name=None, addr=None,)
        images = list()
        imgNotes = dict()
        for pc in self.pcs.all().order_by('-uuid'):
            if pc.lonLat and not result['lonLat']:
                result['lonLat'] = dict(lon=pc.lonLat.x, lat=pc.lonLat.y)

            if pc.image:
                v = str(pc.image)
                if v not in images:
                    images.append(v)
                    imgNotes[v] = None
                if not imgNotes[v] and pc.stext_type == STEXT_TYPE_IMAGE_NOTE:
                    imgNotes[v] = pc.stext.content

            if pc.url:
                v = pc.url.url
                if v not in result['urls']:
                    result['urls'].append(v)

            if pc.fsVenue and not result['fsVenue']:
                result['fsVenue'] = pc.fsVenue.fsVenueId

            if pc.stext:
                if pc.stext_type == STEXT_TYPE_PLACE_NOTE:
                    result['notes'].append(pc.stext.content)
                if pc.stext_type == STEXT_TYPE_PLACE_NAME:
                    if not result['name']:
                        result['name'] = pc.stext.content
                if pc.stext_type == STEXT_TYPE_ADDRESS:
                    if not result['addr']:
                        result['addr'] = pc.stext.content
        result['images'] = [dict(uuid=img, note=imgNotes[img]) for img in images]
        return result


class PlaceContent(models.Model):
    # uuid
    uuid = models.UUIDField(primary_key=True, default=None)

    # node
    place = models.ForeignKey(Place, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')
    vd = models.ForeignKey(VD, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')
    image = models.ForeignKey(Image, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')
    url = models.ForeignKey(Url, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')
    fsVenue = models.ForeignKey(FsVenue, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')
    stext = models.ForeignKey(ShortText, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')

    # value
    lonLat = models.PointField(blank=True, null=True, default=None)
    stext_type = models.SmallIntegerField(blank=True, null=True, default=None)

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
