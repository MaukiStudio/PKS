#-*- coding: utf-8 -*-
from __future__ import unicode_literals

from uuid import UUID
from django.contrib.gis.db import models
from base64 import b16encode
from django.contrib.postgres.fields import JSONField
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance

from account.models import VD
from base.utils import get_timestamp, BIT_ON_8_BYTE, get_uuid_from_ts_vd
from place.post import PostBase
from base.models import Point
from content.models import PlaceName
from geopy.distance import vincenty as vincenty_distance

RADIUS_LOCAL_RANGE = 100


class Place(models.Model):

    lonLat = models.PointField(blank=True, null=True, default=None, geography=True)
    placeName = models.ForeignKey(PlaceName, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='places')

    def __init__(self, *args, **kwargs):
        self._cache_placePost = None
        self._cache_userPost = None
        super(Place, self).__init__(*args, **kwargs)

    def __unicode__(self):
        if self.placeName:
            return self.placeName.content
        return 'No named place object'

    def computePost(self, vd_ids=None):
        # placePost
        pb = PostBase()
        for pp in self.pps.all().filter(uplace=None).order_by('id'):
            pb_new = pp.pb
            pb.update(pb_new, pp.is_add)
        pb.place_id = self.id
        pb.normalize()
        self._cache_placePost = pb

        # userPost
        if vd_ids:
            pb = PostBase()
            for pp in self.pps.filter(vd__in=vd_ids).order_by('id'):
                if pp.is_drop:
                    # TODO : 정책 잡고 구현...
                    # 일단 현재는 UserPlace 에도 is_drop 이 있고 거기서 처리한다는 전제하에 여기에선 무시
                    #pb = PostBase()
                    pass
                else:
                    pb.update(pp.pb, pp.is_add)
            pb.place_id = self.id
            pb.normalize()
            self._cache_userPost = pb

    def _clearCache(self):
        self._cache_placePost = None
        self._cache_userPost = None

    @property
    def placePost(self):
        if not self._cache_placePost:
            self.computePost()
        return self._cache_placePost

    @property
    def userPost(self):
        return self._cache_userPost

    @property
    def _totalPost(self):
        pb = PostBase()
        for pp in self.pps.all().order_by('id'):
            pb.update(pp.pb, pp.is_add)
        pb.place_id = self.id
        pb.normalize()
        return pb


    # TODO : 값들이 서로 모순되는 경우에 대한 처리
    # TODO : 추가로 실시간으로 같은 place 를 찾을 수 있는 상황이라면 곧바로 처리
    # TODO : 장소이름만 단독으로 먼저 붙이고, 그 이후에 좌표를 추가하는 경우 현재 장소화가 안됨.
    @classmethod
    def get_or_create_smart(cls, pb, vd):

        #######################################
        # Direct Placed Part
        #######################################

        # place_id 가 명확히 지정된 경우
        if pb.place_id:
            return cls.objects.get(id=pb.place_id), False

        # Placed by LegacyPlace
        lp = None
        if pb.lps:
            pb.normalize()
            lp = pb.lps[0]
            if lp.place:
                return lp.place, False

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
            if qs and qs[0]:
                _place = qs[0]
                # TODO : 리팩토링 필요
                if lp:
                    lp.place = _place
                    lp.save()
                    PostPiece.objects.create(by_MAMMA=pb.by_MAMMA, place=_place, uplace=None, vd=vd, pb=pb)
                return _place, False


        #######################################
        # Indirect Placed Part
        #######################################

        # Placed by LegacyPlace
        if lp:
            _place = Place.objects.create(lonLat=lonLat, placeName=placeName)
            lp.place = _place
            lp.save()
            PostPiece.objects.create(by_MAMMA=pb.by_MAMMA, place=_place, uplace=None, vd=vd, pb=pb)
            return _place, True

        # Placed by placeName/lonLat
        if placeName and lonLat:
            if not pb.lonLat:
                pb.point = Point(lonLat)
            _place = Place.objects.create(lonLat=lonLat, placeName=placeName)
            PostPiece.objects.create(by_MAMMA=pb.by_MAMMA, place=_place, uplace=None, vd=vd, pb=pb)
            return _place, True

        # last : old_place
        if uplace:
            return uplace.place, False

        return None, False


    @property
    def lonLat_json(self):
        return Point(self.lonLat).json


class UserPlace(models.Model):
    id = models.UUIDField(primary_key=True, default=None)
    vd = models.ForeignKey(VD, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='uplaces')
    place = models.ForeignKey(Place, on_delete=models.SET_DEFAULT, null=True, default=None, related_name='uplaces')
    modified = models.BigIntegerField(blank=True, null=True, default=None)
    lonLat = models.PointField(blank=True, null=True, default=None, geography=True)
    mask = models.SmallIntegerField(blank=True, null=True, default=None)

    def __init__(self, *args, **kwargs):
        self._cache_pb = None
        self._origin = None
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

    def placed(self, place, lonLat=None):
        self.place = place
        self.lonLat = lonLat or place.lonLat or self.lonLat
        self.save()
        for pp in self.pps.all():
            pp.place = place
            pp.save()

    @classmethod
    def get_or_create_smart(cls, pb, vd):
        place, is_place_created = Place.get_or_create_smart(pb, vd)
        uplace = None
        is_uplace_created = False

        # TODO : uplace 좀 더 찾기...
        if pb.uplace_uuid:
            uplace = cls.get_from_uuid(pb.uplace_uuid)
        if not uplace and place:
            uplace = UserPlace.objects.filter(vd_id__in=vd.realOwner_vd_ids, place=place).order_by('id').first()

        lonLat = (place and place.lonLat) or pb.lonLat or (uplace and uplace.lonLat)

        # 실시간 장소화
        if not uplace:
            uplace = cls.objects.create(vd=vd, place=place, lonLat=lonLat)
            is_uplace_created = True
        elif not uplace.place:
            if place:
                uplace.placed(place, lonLat)
        else:
            if place and uplace.place != place:
                uplace.placed(place, lonLat)
                # TODO : 로그 남겨서 Place Merge 시 우선순위 높여 참고하기

        # 결과 처리
        pb.place_id = uplace.place_id
        pb.uplace_uuid = uplace.uuid
        return uplace, is_uplace_created

    def computePost(self, vd_ids=None):
        pb = PostBase()
        for pp in self.pps.all().order_by('id'):
            if pp.is_drop:
                # TODO : 이 부분이 테스트되는 테스트 추가
                pb = PostBase()
            else:
                pb.update(pp.pb, pp.is_add)
        pb.uplace_uuid = self.uuid
        pb.place_id = self.place_id
        pb.normalize()
        self._cache_pb = pb

    def _clearCache(self):
        self._cache_pb = None
        if self.place:
            self.place._clearCache()

    @property
    def userPost(self):
        if not self._cache_pb:
            if self.place:
                # TODO : 이 부분을 테스트하는 코드 추가
                self.place.computePost(self.vd.realOwner_vd_ids + self.vd.realOwner_publisher_ids)
                self._cache_pb = self.place.userPost
            else:
                self.computePost()
        return self._cache_pb

    @property
    def placePost(self):
        return self.place and self.place.placePost

    def _id(self, timestamp):
        vd_id = self.vd_id or 0
        return get_uuid_from_ts_vd(timestamp, vd_id)

    def save(self, *args, **kwargs):
        self.modified = kwargs.pop('timestamp', get_timestamp())
        if not self.id:
            self.id = self._id(self.modified)
        if not self.lonLat:
            self.lonLat = (self.place and self.place.lonLat) or None
        if not self.mask:
            self.mask = 0
        super(UserPlace, self).save(*args, **kwargs)

    @property
    def created(self):
        return self.id and (int(self.id) >> 8*8) & BIT_ON_8_BYTE

    @property
    def lonLat_json(self):
        return Point(self.lonLat).json

    @property
    def is_drop(self):
        return ((self.mask or 0) & 1) != 0
    @is_drop.setter
    def is_drop(self, value):
        if value:
            self.mask = (self.mask or 0) | 1
        else:
            self.mask = (self.mask or 0) & (~1)

    @property
    def origin(self):
        return self._origin
    @origin.setter
    def origin(self, value):
        self._origin = value

    @property
    def distance_from_origin(self):
        if not self.origin or not self.lonLat:
            return None
        m = vincenty_distance(self.origin, self.lonLat).meters
        m = int(round(m/10.0))*10.0
        if m < 1000.0:
            return '%dm' % m
        k = int(round(m/100.0))/10.0
        return '%.1fkm' % k

    # Negative Log Likelyhood
    # Test in tag/test_models.py
    # TODO : 튜닝
    # P(t1,t2,...,tn | place) = P(t1|place)P(t2|t1,place)...P(tn|t1,t2,...,place)
    def NLL(self, tags):
        from math import log
        uplace_tags = list(self.tags.all())
        tags_in_utags = [tag for tag in tags if tag in uplace_tags]

        place_tags = []
        ptags = []
        tags_in_ptags = []
        if self.place:
            place_ptags = list(self.place.ptags.all())
            place_tags = [ptag.tag for ptag in place_ptags]
            ptags = [ptag for ptag in place_ptags if ptag.tag in tags and ptag.tag not in tags_in_utags]
            tags_in_ptags = [ptag.tag for ptag in ptags]
        tags_others = list(set([tag for tag in tags if tag not in tags_in_utags and tag not in tags_in_ptags]))

        # utags 는 모두 prob = 1.0 --> NLL = 0.0
        result = 0.0

        # ptags
        for ptag in ptags:
            # place 가 결정되어 있으면 ti, tj (i != j) 는 서로 조건부 독립
            # So P(ti|t1,t2,...,t(i-1),place) = P(ti|place)
            result -= log(ptag.prob)

        # tags_others
        # place 에 해당 tag 들에 대한 정보가 전혀 없다면, place 와 ti 는 서로 독립으로 볼 수 있다???
        # TODO : 맞는지 확인. 왠지 아닌 것 같긴 한데 Naive Bayse 의 조건부독립 근사처럼 근사가 가능할 듯...
        # So P(ti|t1,t2,...,t(i-1),place) = P(ti|t1,t2,...,t(i-1)) if place do not have t1, t2, ..., ti
        for tag in tags_others:
            Ds = list(set(uplace_tags+place_tags))
            # 조건부 독립으로 가정하고 tags_others 의 있는 tag 들을 쪼개어 곱함
            prob = tag.posterior(Ds)
            result -= log(prob)

        '''
        print(tags)
        print(tags_in_utags)
        print(tags_in_ptags)
        print(tags_others)
        #'''
        return result


class PostPiece(models.Model):
    # id
    id = models.UUIDField(primary_key=True, default=None)

    # properties mask
    mask = models.SmallIntegerField(blank=True, null=True, default=None)

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
        return get_uuid_from_ts_vd(timestamp, vd_id)

    def save(self, *args, **kwargs):
        if not self.id:
            timestamp = kwargs.pop('timestamp', get_timestamp())
            self.id = self._id(timestamp)
        if not self.mask:
            self.mask = 0
        if not self.place and (self.uplace and self.uplace.place):
            self.place = self.uplace.place

        # Machine 이 포스팅한 경우 vd를 None 으로. 단, vd값이 넘어온 경우 id값 계산시엔 활용 (위에서 이미 id 계산)
        if self.by_MAMMA:
            self.vd = None
        super(PostPiece, self).save(*args, **kwargs)

    @property
    def timestamp(self):
        return (int(self.id) >> 8*8) & BIT_ON_8_BYTE

    @property
    def is_remove(self):
        return ((self.mask or 0) & 1) != 0
    @is_remove.setter
    def is_remove(self, value):
        if value:
            self.mask = (self.mask or 0) | 1
        else:
            self.mask = (self.mask or 0) & (~1)

    @property
    def is_add(self):
        return not self.is_remove

    @property
    def by_MAMMA(self):
        return ((self.mask or 0) & 2) != 0
    @by_MAMMA.setter
    def by_MAMMA(self, value):
        if value:
            self.mask = (self.mask or 0) | 2
        else:
            self.mask = (self.mask or 0) & (~2)

    @property
    def is_drop(self):
        return ((self.mask or 0) & 4) != 0
    @is_drop.setter
    def is_drop(self, value):
        if value:
            self.mask = (self.mask or 0) | 4
        else:
            self.mask = (self.mask or 0) & (~4)

    @property
    def pb(self):
        pb1 = PostBase(self.data, self.timestamp)
        '''
        if pb1.iplace_uuid:
            iplace = UserPlace.get_from_uuid(pb1.iplace_uuid)
            if iplace:
                pb1.update(iplace.userPost)
        #'''
        return pb1
    @pb.setter
    def pb(self, value):
        self.data = value.sjson
