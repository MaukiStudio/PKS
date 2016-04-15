#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from uuid import UUID
from random import randrange
from django.contrib.gis.db import models
from base64 import b16encode
from django.contrib.postgres.fields import JSONField

from account.models import VD
from base.utils import get_timestamp, BIT_ON_8_BYTE
from place.post import Post
from image.models import Image
from url.models import Url
from content.models import LegacyPlace, ShortText, PhoneNumber


class Place(models.Model):

    vds = models.ManyToManyField(VD, through='UserPlace', through_fields=('place', 'vd'), related_name='places')
    lonLat = models.PointField(blank=True, null=True, default=None, geography=True)

    def __init__(self, *args, **kwargs):
        self._post_cache = None
        super(Place, self).__init__(*args, **kwargs)

    def computePost(self):
        post = None
        pcs = None

        # TODO : 튜닝 필요;;;
        for uplace in self.uplaces.all():
            pcs = (pcs and pcs | uplace.pcs.all()) or uplace.pcs.all()
        for pc in pcs.order_by('-id'):
            if not post:
                post = Post()
                post.set_place_id(self.id)
            post.add_pc(pc)
        self._post_cache = post

    def clearCache(self):
        self._post_cache = None

    @property
    def placePost(self):
        if not self._post_cache:
            self.computePost()
        return self._post_cache

    @classmethod
    def get_from_post(cls, post):
        # post 에 place_id 가 있는 경우
        if 'place_id' in post.json and post.json['place_id']:
            return cls.objects.get(id=post.json['place_id'])
        # post 에 uplace_uuid 가 있는 경우
        if 'uplace_uuid' in post.json and post.json['uplace_uuid']:
            uplace = UserPlace.get_from_uuid(post.json['uplace_uuid'])
            if uplace.place:
                return uplace.place
        # post 에 lps 가 있는 경우 : 현재는 1개 넘어오는 것만 구현
        if 'lps' in post.json and post.json['lps'] and post.json['lps'][0]:
            if len(post.json['lps']) > 1:
                raise NotImplementedError
            lp = LegacyPlace.get_from_json(post.json['lps'][0])
            if lp.place:
                return lp.place

            _place = Place(lonLat=post.lonLat)
            _place.save()
            lp.place = _place
            lp.save()
            return lp.place
        # TODO : 추가로 실시간으로 같은 place 를 찾을 수 있는 상황이라면 곧바로 처리

        return None


class UserPlace(models.Model):
    id = models.UUIDField(primary_key=True, default=None)
    vd = models.ForeignKey(VD, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='uplaces')
    place = models.ForeignKey(Place, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='uplaces')
    modified = models.BigIntegerField(blank=True, null=True, default=None)
    lonLat = models.PointField(blank=True, null=True, default=None, geography=True)

    def __init__(self, *args, **kwargs):
        self._post_cache = None
        super(UserPlace, self).__init__(*args, **kwargs)

    @property
    def uuid(self):
        return '%s.%s' % (b16encode(self.id.bytes), 'uplace',)

    @classmethod
    def get_from_uuid(cls, _uuid):
        splits = _uuid.split('.')
        if splits[1] != 'uplace':
            raise ValueError
        _id = UUID(splits[0])
        return cls.objects.get(id=_id)

    @classmethod
    def get_from_post(cls, post, vd):
        # TODO : uplace 좀 더 찾기...
        place = Place.get_from_post(post)
        uplace = None
        if 'uplace_uuid' in post.json and post.json['uplace_uuid']:
            uplace = cls.get_from_uuid(post.json['uplace_uuid'])
        if not uplace and place:
            # TODO : 이 부분이 테스트되는 테스트 코드 추가하기
            uplace = UserPlace.objects.filter(vd=vd, place=place).order_by('id').first()

        # Place 처리
        if not uplace:
            uplace = cls(vd=vd, place=place, lonLat=post.lonLat)
            uplace.save()
        elif not uplace.place:
            uplace.place = place
            uplace.save()
        else:
            # TODO : raise 대신 복구 루틴 구현
            if place and uplace.place != place:
                raise NotImplementedError('Place / UserPlace mismatch')

        # 결과 처리
        return uplace

    def computePost(self):
        post = None
        for pc in self.pcs.all().order_by('-id'):
            if not post:
                post = Post()
                post.set_uplace_uuid(self.uuid)
                post.set_place_id(self.place_id)
            post.add_pc(pc)
        self._post_cache = post

    def clearCache(self):
        self._post_cache = None
        if self.place:
            self.place.clearCache()

    @property
    def userPost(self):
        if not self._post_cache:
            self.computePost()
        return self._post_cache

    @property
    def placePost(self):
        return self.place and self.place.placePost

    def _id(self, timestamp):
        vd_id = self.vd_id or 0
        hstr = hex((timestamp << 8*8) | (vd_id << 2*8) | randrange(0, 65536))[2:-1]
        return UUID(hstr.rjust(32, b'0'))

    def save(self, *args, **kwargs):
        self.modified = kwargs.pop('timestamp', get_timestamp())
        if not self.id:
            self.id = self._id(self.modified)
        if not self.lonLat:
            self.lonLat = (self.place and self.place.lonLat) or None
        super(UserPlace, self).save(*args, **kwargs)

    @property
    def created(self):
        return self.id and (int(self.id) >> 8*8) & BIT_ON_8_BYTE


class PlaceContent(models.Model):
    # id
    id = models.UUIDField(primary_key=True, default=None)

    # node
    uplace = models.ForeignKey(UserPlace, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pcs')
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


class PostPiece(models.Model):
    # id
    id = models.UUIDField(primary_key=True, default=None)

    # mode : 0bit:0/add,1/remove, 1bit:is_MAMMA
    # so... : 0/add, 1/remove, 2/add_by_MAMMA, ...
    type_mask = models.SmallIntegerField(blank=True, null=True, default=None)

    # ref
    uplace = models.ForeignKey(UserPlace, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pps')
    place = models.ForeignKey(Place, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pps')

    # MAMMA 등 Machine 이 포스팅한 것은 None 으로 세팅됨
    vd = models.ForeignKey(VD, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='pps')

    # json
    data = JSONField(blank=True, null=True, default=None, db_index=True)

    def _id(self, timestamp):
        vd_id = self.vd_id or 0
        hstr = hex((timestamp << 8*8) | (vd_id << 2*8) | randrange(0, 65536))[2:-1]
        return UUID(hstr.rjust(32, b'0'))

    def save(self, *args, **kwargs):
        if not self.id:
            timestamp = kwargs.pop('timestamp', get_timestamp())
            self.id = self._id(timestamp)
        if not self.type_mask:
            self.type_mask = 0
        super(PostPiece, self).save(*args, **kwargs)

    @property
    def timestamp(self):
        return (int(self.id) >> 8*8) & BIT_ON_8_BYTE

    @property
    def is_add(self):
        return (self.type_mask & 1) == 0

    @property
    def is_remove(self):
        return (self.type_mask & 1) == 1
