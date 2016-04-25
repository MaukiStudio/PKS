#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from uuid import UUID
from random import randrange
from django.contrib.gis.db import models
from base64 import b16encode
from django.contrib.postgres.fields import JSONField
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance

from account.models import VD
from base.utils import get_timestamp, BIT_ON_8_BYTE
from place.post import PostBase
from base.models import Point
from content.models import PlaceName

RADIUS_LOCAL_RANGE = 100


class Place(models.Model):

    lonLat = models.PointField(blank=True, null=True, default=None, geography=True)
    placeName = models.ForeignKey(PlaceName, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='places')

    def __init__(self, *args, **kwargs):
        self._pb_cache = None
        super(Place, self).__init__(*args, **kwargs)

    def __unicode__(self):
        if self.placeName:
            return self.placeName.content
        return 'No named place object'

    def computePost(self):
        pb = None
        for pp in self.pps.all().order_by('id'):
            pb_new = PostBase(pp.data, pp.timestamp)
            if not pb:
                if pp.is_add:
                    pb = pb_new
            else:
                pb.update(pb_new, pp.is_add)
        if pb:
            pb.place_id = self.id
        self._pb_cache = pb

    def clearCache(self):
        self._pb_cache = None

    @property
    def placePost(self):
        if not self._pb_cache:
            self.computePost()
        return self._pb_cache


    # TODO : 값들이 서로 모순되는 경우에 대한 처리
    # TODO : 추가로 실시간으로 같은 place 를 찾을 수 있는 상황이라면 곧바로 처리
    # TODO : 장소이름만 단독으로 먼저 붙이고, 그 이후에 좌표를 추가하는 경우 현재 장소화가 안됨.
    @classmethod
    def get_from_post(cls, pb, vd):

        #######################################
        # Direct Placed Part
        #######################################

        # place_id 가 명확히 지정된 경우
        if pb.place_id:
            return cls.objects.get(id=pb.place_id)

        # Placed by LegacyPlace
        lp = None
        if pb.lps:
            pb.sort()
            lp = pb.lps[0]
            if lp.place:
                return lp.place

        # uplace, lonLat 조회
        uplace = None
        if pb.uplace_uuid:
            uplace = UserPlace.get_from_uuid(pb.uplace_uuid)
        lonLat = pb.lonLat or (uplace and uplace.lonLat)

        # Placed by placeName/lonLat
        placeName = pb.name
        if placeName and lonLat:
            qs = Place.objects.filter(placeName=placeName)\
                .filter(lonLat__distance_lte=(lonLat, D(m=RADIUS_LOCAL_RANGE)))\
                .annotate(distance=Distance('lonLat', lonLat)).order_by('distance')
            if qs:
                _place = qs[0]
                # TODO : 리팩토링 필요
                if lp:
                    lp.place = _place
                    lp.save()
                    PostPiece.objects.create(type_mask=2, place=_place, uplace=None, vd=vd, data=pb.json)
                return _place


        #######################################
        # Indirect Placed Part
        #######################################

        # Placed by LegacyPlace
        if lp:
            _place = Place(lonLat=lonLat, placeName=placeName)
            _place.save()
            lp.place = _place
            lp.save()
            PostPiece.objects.create(type_mask=2, place=_place, uplace=None, vd=vd, data=pb.json)
            return _place

        # Placed by placeName/lonLat
        if placeName and lonLat:
            if not pb.lonLat:
                pb.point = Point(lonLat.x, lonLat.y)
            _place = Place(lonLat=lonLat, placeName=placeName)
            _place.save()
            PostPiece.objects.create(type_mask=2, place=_place, uplace=None, vd=vd, data=pb.json)
            return _place

        # last : old_place
        if uplace:
            return uplace.place

        return None


    @property
    def lonLat_json(self):
        return Point(self.lonLat.x, self.lonLat.y).json


class UserPlace(models.Model):
    id = models.UUIDField(primary_key=True, default=None)
    vd = models.ForeignKey(VD, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='uplaces')
    place = models.ForeignKey(Place, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='uplaces')
    modified = models.BigIntegerField(blank=True, null=True, default=None)
    lonLat = models.PointField(blank=True, null=True, default=None, geography=True)

    def __init__(self, *args, **kwargs):
        self._pb_cache = None
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
    # TODO : save() 너무 많이 함. 튜닝 필요
    def get_from_post(cls, pb, vd):
        place = Place.get_from_post(pb, vd)
        uplace = None

        # TODO : uplace 좀 더 찾기...
        if pb.uplace_uuid:
            uplace = cls.get_from_uuid(pb.uplace_uuid)
        if not uplace and place:
            # TODO : 이 부분이 테스트되는 테스트 코드 추가하기
            uplace = UserPlace.objects.filter(vd=vd, place=place).order_by('id').first()

        lonLat = (place and place.lonLat) or pb.lonLat

        # 실시간 장소화
        if not uplace:
            uplace = cls(vd=vd, place=place, lonLat=lonLat)
            uplace.save()
        elif not uplace.place:
            uplace.place = place
            uplace.lonLat = lonLat
            uplace.save()
        else:
            if place and uplace.place != place:
                uplace.place = place
                uplace.lonLat = lonLat
                uplace.save()
                # TODO : 로그 남겨서 Place Merge 시 우선순위 높여 참고하기

        # 결과 처리
        pb.place_id = uplace.place_id
        pb.uplace_uuid = uplace.uuid
        return uplace

    def computePost(self):
        pb = None
        for pp in self.pps.all().order_by('id'):
            pb_new = PostBase(pp.data, pp.timestamp)
            if not pb:
                if pp.is_add:
                    pb = pb_new
            else:
                pb.update(pb_new, pp.is_add)
        if pb:
            pb.uplace_uuid = self.uuid
            pb.place_id = self.place_id
        self._pb_cache = pb

    def clearCache(self):
        self._pb_cache = None
        if self.place:
            self.place.clearCache()

    @property
    def userPost(self):
        if not self._pb_cache:
            self.computePost()
        return self._pb_cache

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

    @property
    def lonLat_json(self):
        return Point(self.lonLat.x, self.lonLat.y).json


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
    # 허나 ID 발급을 위해 vd 자체는 세팅해서 넘겨야 한다
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

        # Machine 이 포스팅한 경우 vd를 None 으로. 단, vd값이 넘어온 경우 id값 계산시엔 활용
        if self.type_mask >= 2:
            self.vd = None
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
