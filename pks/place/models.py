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

# stxt_type
STXT_TYPE_PLACE_NOTE = 1
STXT_TYPE_PLACE_NAME = 2
STXT_TYPE_ADDRESS = 3
STXT_TYPE_IMAGE_NOTE = 4


class Place(models.Model):

    def __init__(self, *args, **kwargs):
        self.post_cache = None
        super(Place, self).__init__(*args, **kwargs)

    def computePost(self, myVds):
        if self.post_cache: return

        result = [None, None]
        images = [None, None]
        imgNotes = [None, None]
        for postType in (0, 1):
            result[postType] = dict(place_id=self.id, lonLat=None, images=None, urls=list(), fsVenue=None, notes=list(), name=None, addr=None,)
            images[postType] = list()
            imgNotes[postType] = dict()

        for pc in self.pcs.all().order_by('-id'):
            for postType in (0, 1):
                if postType == 0 and pc.vd_id not in myVds:
                    continue

                if pc.lonLat and not result[postType]['lonLat']:
                    result[postType]['lonLat'] = dict(lon=pc.lonLat.x, lat=pc.lonLat.y)

                if pc.image:
                    v = pc.image.content
                    if v not in images[postType]:
                        images[postType].append(v)
                        imgNotes[postType][v] = None
                    if pc.stxt_type == STXT_TYPE_IMAGE_NOTE and not imgNotes[postType][v]:
                        imgNotes[postType][v] = pc.stxt.content

                if pc.url:
                    v = pc.url.content
                    if v not in result[postType]['urls']:
                        result[postType]['urls'].append(v)

                if pc.fsVenue and not result[postType]['fsVenue']:
                    v = pc.fsVenue.content
                    result[postType]['fsVenue'] = result[postType]['fsVenue'] or v

                if pc.stxt:
                    v = pc.stxt.content
                    if pc.stxt_type == STXT_TYPE_PLACE_NOTE:
                        result[postType]['notes'].append(v)
                    if pc.stxt_type == STXT_TYPE_PLACE_NAME:
                        result[postType]['name'] = result[postType]['name'] or v
                    if pc.stxt_type == STXT_TYPE_ADDRESS:
                        result[postType]['addr'] = result[postType]['addr'] or v

        for postType in (0, 1):
            result[postType]['images'] = [dict(uuid=img, note=imgNotes[postType][img]) for img in images[postType]]
        self.post_cache = dict(userPost=result[0], placePost=result[1])

    @property
    def _userPost(self):
        return self.post_cache['userPost']

    @property
    def placePost(self):
        return self.post_cache['placePost']


class PlaceContent(models.Model):
    # id
    id = models.UUIDField(primary_key=True, default=None)

    # node
    place = models.ForeignKey(Place, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')
    vd = models.ForeignKey(VD, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')
    image = models.ForeignKey(Image, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')
    url = models.ForeignKey(Url, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')
    fsVenue = models.ForeignKey(FsVenue, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')
    stxt = models.ForeignKey(ShortText, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')

    # value
    lonLat = models.PointField(blank=True, null=True, default=None)
    stxt_type = models.SmallIntegerField(blank=True, null=True, default=None)

    def set_id(self):
        timestamp = int(round(Delorean().epoch*1000))
        vd_id = self.vd_id or 0
        hstr = hex((1 << 16*8-2) | (timestamp << 8*8-2) | (vd_id << 2*8-2) | randrange(0, 65536/4))[2:-1]
        self.id = UUID(hstr.rjust(32, b'0'))

    def save(self, *args, **kwargs):
        if not self.id:
            self.set_id()
        super(PlaceContent, self).save(*args, **kwargs)


class UserPost(models.Model):

    vd = models.ForeignKey(VD, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='uposts')
    place = models.ForeignKey(Place, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='uposts')

    class Meta:
        unique_together = ('vd', 'place')

    @property
    def userPost(self):
        self.place.computePost([self.vd.id])
        return self.place._userPost
