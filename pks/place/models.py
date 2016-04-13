#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from uuid import UUID
from random import randrange
from django.contrib.gis.db import models

from account.models import VD
from image.models import Image
from url.models import Url
from content.models import LegacyPlace, ShortText, PhoneNumber
from base.utils import get_timestamp, BIT_ON_8_BYTE


class Place(models.Model):

    vds = models.ManyToManyField(VD, through='UserPlace', through_fields=('place', 'vd'), related_name='places')
    lonLat = models.PointField(blank=True, null=True, default=None, geography=True)

    def __init__(self, *args, **kwargs):
        self._posts_cache = None
        super(Place, self).__init__(*args, **kwargs)

    def computePost(self, my_vd_ids):
        if self._posts_cache: return
        posts = [None, None]

        for pc in self.pcs.all().order_by('-id'):
            for postType in (0, 1):
                if postType == 0 and pc.vd_id not in my_vd_ids:
                    continue
                if not posts[postType]:
                    from place.post import Post
                    posts[postType] = Post(self)
                posts[postType].add_pc(pc)

        self._posts_cache = posts

    def clearCache(self):
        self._posts_cache = None

    @property
    def userPost(self):
        return self._posts_cache[0]

    @property
    def placePost(self):
        return self._posts_cache[1]


class PlaceContent(models.Model):
    # id
    id = models.UUIDField(primary_key=True, default=None)

    # node
    place = models.ForeignKey(Place, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')
    vd = models.ForeignKey(VD, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')
    image = models.ForeignKey(Image, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')
    url = models.ForeignKey(Url, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')
    lp = models.ForeignKey(LegacyPlace, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')
    stxt = models.ForeignKey(ShortText, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')
    phone = models.ForeignKey(PhoneNumber, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')

    # value
    lonLat = models.PointField(blank=True, null=True, default=None, geography=True, db_index=False)
    stxt_type = models.SmallIntegerField(blank=True, null=True, default=None)

    def _id(self, timestamp):
        vd_id = self.vd_id or 0
        hstr = hex((timestamp << 8*8) | (vd_id << 2*8) | randrange(0, 65536))[2:-1]
        return UUID(hstr.rjust(32, b'0'))

    def save(self, *args, **kwargs):
        if not self.id:
            timestamp = kwargs.pop('timestamp', get_timestamp())
            self.id = self._id(timestamp)
        super(PlaceContent, self).save(*args, **kwargs)

    @property
    def timestamp(self):
        return (int(self.id) >> 8*8) & BIT_ON_8_BYTE


class UserPlace(models.Model):
    id = models.UUIDField(primary_key=True, default=None)
    vd = models.ForeignKey(VD, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='uplaces')
    place = models.ForeignKey(Place, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='uplaces')
    modified = models.BigIntegerField(blank=True, null=True, default=None)
    lonLat = models.PointField(blank=True, null=True, default=None, geography=True)

    @property
    def userPost(self):
        vd_ids = self.vd.realOwner_vd_ids
        self.place.computePost(vd_ids)
        return self.place.userPost

    @property
    def placePost(self):
        vd_ids = self.vd.realOwner_vd_ids
        self.place.computePost(vd_ids)
        return self.place.placePost

    def _id(self, timestamp):
        vd_id = self.vd_id or 0
        hstr = hex((timestamp << 8*8) | (vd_id << 2*8) | randrange(0, 65536))[2:-1]
        return UUID(hstr.rjust(32, b'0'))

    def save(self, *args, **kwargs):
        self.modified = kwargs.pop('modified', get_timestamp())
        if not self.id:
            self.id = self._id(self.modified)
        if not self.lonLat:
            self.lonLat = (self.place and self.place.lonLat) or None
        super(UserPlace, self).save(*args, **kwargs)

    @property
    def created(self):
        return self.id and (int(self.id) >> 8*8) & BIT_ON_8_BYTE
