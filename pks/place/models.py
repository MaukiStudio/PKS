#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from uuid import UUID
from random import randrange
from django.contrib.gis.db import models

from account.models import VD
from image.models import Image
from url.models import Url
from content.models import LegacyPlace, ShortText
from base.utils import get_timestamp

# stxt_type
STXT_TYPE_PLACE_NOTE = 1
STXT_TYPE_PLACE_NAME = 2
STXT_TYPE_ADDRESS = 3
STXT_TYPE_IMAGE_NOTE = 4
STXT_TYPE_REMOVE_CONTENT = 255


class Place(models.Model):

    vds = models.ManyToManyField(VD, through='UserPost', through_fields=('place', 'vd'), related_name='places')

    def __init__(self, *args, **kwargs):
        self.post_cache = None
        super(Place, self).__init__(*args, **kwargs)

    def computePost(self, myVds):
        if self.post_cache: return

        result = [None, None]
        images = [None, None]
        imgNotes = [None, None]
        for postType in (0, 1):
            result[postType] = dict(place_id=self.id, lonLat=None, images=None, urls=list(), lp=None, notes=list(), name=None, addr=None,)
            images[postType] = list()
            imgNotes[postType] = dict()

        # TODO : 향후 삭제 처리 구현 필요. 특정 Content 를 삭제하고 싶은 경우 노트타입을 삭제로 붙임. 이 노트타입은 노트뿐만 아니라 다른 Content 에도 적용
        for pc in self.pcs.all().order_by('-id'):
            for postType in (0, 1):
                if postType == 0 and pc.vd_id not in myVds:
                    continue

                if pc.lonLat and not result[postType]['lonLat']:
                    result[postType]['lonLat'] = dict(lon=pc.lonLat.x, lat=pc.lonLat.y)

                if pc.image:
                    uuid = pc.image.uuid
                    dl = images[postType]
                    if uuid not in [d['uuid'] for d in dl]:
                        dl.append(dict(uuid=uuid, content=pc.image.content))
                        imgNotes[postType][uuid] = None
                    if pc.stxt_type == STXT_TYPE_IMAGE_NOTE and pc.stxt.content and not imgNotes[postType][uuid]:
                        imgNotes[postType][uuid] = dict(uuid=pc.stxt.uuid, content=pc.stxt.content)

                if pc.url:
                    uuid = pc.url.uuid
                    dl = result[postType]['urls']
                    if uuid not in [d['uuid'] for d in dl]:
                        dl.append(dict(uuid=uuid, content=pc.url.content))

                if pc.lp and not result[postType]['lp']:
                    uuid = pc.lp.uuid
                    result[postType]['lp'] = dict(uuid=uuid, content=pc.lp.content)

                if pc.stxt:
                    uuid = pc.stxt.uuid
                    if pc.stxt_type == STXT_TYPE_PLACE_NOTE:
                        dl = result[postType]['notes']
                        if uuid not in [d['uuid'] for d in dl]:
                            dl.append(dict(uuid=uuid, content=pc.stxt.content))
                    if pc.stxt_type == STXT_TYPE_PLACE_NAME and not result[postType]['name']:
                        result[postType]['name'] = dict(uuid=uuid, content=pc.stxt.content)
                    if pc.stxt_type == STXT_TYPE_ADDRESS and not result[postType]['addr']:
                        result[postType]['addr'] = dict(uuid=uuid, content=pc.stxt.content)

        for postType in (0, 1):
            result[postType]['images'] = [dict(uuid=uuid, content=content, note=imgNotes[postType][uuid]) for (uuid, content) in [(d['uuid'], d['content']) for d in images[postType]]]
        self.post_cache = dict(userPost=result[0], placePost=result[1])

    @property
    def userPost(self):
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
    lp = models.ForeignKey(LegacyPlace, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')
    stxt = models.ForeignKey(ShortText, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')

    # value
    lonLat = models.PointField(blank=True, null=True, default=None)
    stxt_type = models.SmallIntegerField(blank=True, null=True, default=None)

    def set_id(self, timestamp):
        vd_id = self.vd_id or 0
        hstr = hex((timestamp << 8*8) | (vd_id << 2*8) | randrange(0, 65536))[2:-1]
        self.id = UUID(hstr.rjust(32, b'0'))

    def save(self, *args, **kwargs):
        if not self.id:
            timestamp = kwargs.pop('timestamp', get_timestamp())
            self.set_id(timestamp)
        super(PlaceContent, self).save(*args, **kwargs)


class UserPost(models.Model):

    vd = models.ForeignKey(VD, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='uposts')
    place = models.ForeignKey(Place, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='uposts')

    class Meta:
        unique_together = ('vd', 'place')

    @property
    def userPost(self):
        # TODO : [self.vd.id] 부분을 [ru.vds.id] 로 변경 구현. 성능을 위해 세션도 사용할 것
        self.place.computePost([self.vd.id])
        return self.place.userPost

    @property
    def placePost(self):
        # TODO : [self.vd.id] 부분을 [ru.vds.id] 로 변경 구현. 성능을 위해 세션도 사용할 것
        self.place.computePost([self.vd.id])
        return self.place.placePost
