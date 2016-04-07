#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from json import loads as json_loads
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
STXT_TYPE_POS_DESC = 3
STXT_TYPE_IMAGE_NOTE = 4
STXT_TYPE_ADDRESS = 5
STXT_TYPE_REMOVE_CONTENT = 255

# bit mask for id (timestamp, vd)
BIT_ON_8_BYTE = int('0xFFFFFFFFFFFFFFFF', 16)
BIT_ON_6_BYTE = int('0x0000FFFFFFFFFFFF', 16)


# TODO : 향후 삭제 처리 구현 필요. 특정 Content 를 삭제하고 싶은 경우 노트타입을 삭제로 붙임. 이 노트타입은 노트뿐만 아니라 다른 Content 에도 적용
class Post(object):

    def __init__(self, value=None):
        t = type(value)
        if t is int or t is long:
            self.json = dict(place_id=value, lonLat=None, images=list(), urls=list(), lps=list(),
                             name=None, notes=list(), posDesc=None, addrs=list(), phone=None,)
        elif t is unicode or t is str:
            self.json = json_loads(value)
        elif t is dict:
            self.json = value
        else:
            raise NotImplementedError

    def add_pc(self, pc):
        if pc.lonLat and not self.json['lonLat']:
            self.json['lonLat'] = dict(lon=pc.lonLat.x, lat=pc.lonLat.y, timestamp=pc.timestamp)

        if pc.image:
            uuid = pc.image.uuid
            dl = self.json['images']
            if uuid not in [d['uuid'] for d in dl]:
                dl.append(dict(uuid=uuid, content=pc.image.content, note=None, timestamp=pc.timestamp))
            if pc.stxt_type == STXT_TYPE_IMAGE_NOTE and pc.stxt.content:
                d = None
                for dt in dl:
                    if dt['uuid'] == uuid:
                        d = dt
                        break
                if d and not d['note']:
                    d['note'] = dict(uuid=pc.stxt.uuid, content=pc.stxt.content, timestamp=pc.timestamp)

        if pc.url:
            uuid = pc.url.uuid
            dl = self.json['urls']
            if uuid not in [d['uuid'] for d in dl]:
                dl.append(dict(uuid=uuid, content=pc.url.content, timestamp=pc.timestamp))

        if pc.lp:
            uuid = pc.lp.uuid
            dl = self.json['lps']
            if uuid not in [d['uuid'] for d in dl]:
                dl.append(dict(uuid=uuid, content=pc.lp.content, timestamp=pc.timestamp))

        if pc.stxt:
            uuid = pc.stxt.uuid
            if pc.stxt_type == STXT_TYPE_PLACE_NAME:
                if not self.json['name']:
                    self.json['name'] = dict(uuid=uuid, content=pc.stxt.content, timestamp=pc.timestamp)
            elif pc.stxt_type == STXT_TYPE_PLACE_NOTE:
                dl = self.json['notes']
                if uuid not in [d['uuid'] for d in dl]:
                    dl.append(dict(uuid=uuid, content=pc.stxt.content, timestamp=pc.timestamp))
            elif pc.stxt_type == STXT_TYPE_POS_DESC:
                if not self.json['posDesc']:
                    self.json['posDesc'] = dict(uuid=uuid, content=pc.stxt.content, timestamp=pc.timestamp)
            elif pc.stxt_type == STXT_TYPE_ADDRESS:
                dl = self.json['addrs']
                if len(dl) <= 2 and uuid not in [d['uuid'] for d in dl]:
                    dl.append(dict(uuid=uuid, content=pc.stxt.content, timestamp=pc.timestamp))
            elif pc.stxt_type == STXT_TYPE_IMAGE_NOTE or pc.stxt_type is None:
                pass
            else:
                print(pc.stxt_type)
                raise NotImplementedError


    def isSubsetOf(self, other):
        def isSubsetOf_dict(d1, d2):
            if not d1: return True
            elif not d2: return False
            elif type(d2) is not dict: return False

            for key, value in d1.iteritems():
                if not value:
                    continue
                elif type(value) is dict:
                    if key not in d2 or not isSubsetOf_dict(value, d2[key]):
                        return False
                elif type(value) is list:
                    if key not in d2 or not isSubsetOf_list(value, d2[key]):
                        return False
                else:
                    if key not in d2 or value != d2[key]:
                        return False
            return True
        def isSubsetOf_list(l1, l2):
            if not l1: return True
            elif not l2: return False
            elif type(l2) is not list: return False
            elif len(l1) != len(l2): return False

            for key, value in enumerate(l1):
                if not value:
                    if l2[key]:
                        return False
                elif type(value) is dict:
                    if not isSubsetOf_dict(value, l2[key]):
                        return False
                elif type(value) is list:
                    if not isSubsetOf_list(value, l2[key]):
                        return False
                else:
                    if value != l2[key]:
                        return False
            return True
        return isSubsetOf_dict(self.json, other.json)


class Place(models.Model):

    vds = models.ManyToManyField(VD, through='UserPlace', through_fields=('place', 'vd'), related_name='places')

    def __init__(self, *args, **kwargs):
        self.post_cache = None
        super(Place, self).__init__(*args, **kwargs)

    def computePost(self, myVds):
        if self.post_cache: return

        posts = [Post(self.id), Post(self.id)]

        for pc in self.pcs.all().order_by('-id'):
            for postType in (0, 1):
                if postType == 0 and pc.vd_id not in myVds:
                    continue
                posts[postType].add_pc(pc)

        self.post_cache = posts

    def clearCache(self):
        self.post_cache = None

    @property
    def userPost(self):
        return self.post_cache[0]

    @property
    def placePost(self):
        return self.post_cache[1]


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

    @property
    def timestamp(self):
        return (int(self.id) >> 8*8) & BIT_ON_8_BYTE


class UserPlace(models.Model):

    vd = models.ForeignKey(VD, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='uplaces')
    place = models.ForeignKey(Place, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='uplaces')

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
